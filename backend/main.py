"""
main.py — GeoRisk Intelligence Platform — FastAPI entry point
─────────────────────────────────────────────────────────────
Run:  python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs
"""
import logging
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db, get_db_session

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("GeoRisk Intelligence starting up...")

    # 1. Create / migrate DB tables
    init_db()

    # 2. Seed reference data (countries, politicians)
    _seed_reference_data()

    # 3. Seed demo data if enabled and DB is empty
    if settings.seed_demo_data:
        try:
            from seed_demo import run_seed
            run_seed()
        except Exception as e:
            logger.error(f"Demo seed failed: {e}")

    # 4. Pre-warm the NLP inference service and run demo validation
    #    This loads RoBERTa + LR at startup so the first API call is fast.
    try:
        import threading
        def _warmup_nlp():
            import time
            time.sleep(2)
            try:
                from services.nlp_inference import get_nlp_service
                svc = get_nlp_service()
                if svc.is_ready():
                    # Run demo validation sentences to confirm pipeline works
                    from scoring.demo_dataset import score_validation_sentences
                    results = score_validation_sentences()
                    correct = sum(1 for r in results if r["correct"])
                    logger.info(
                        f"NLP pipeline warm-up complete. "
                        f"Demo validation: {correct}/{len(results)} correct. "
                        f"Scores: {[r['risk_score'] for r in results]}"
                    )
                else:
                    logger.warning("NLP service not ready after warm-up")
            except Exception as e:
                logger.error(f"NLP warm-up failed: {e}")
        threading.Thread(target=_warmup_nlp, daemon=True).start()
    except Exception as e:
        logger.error(f"NLP warm-up thread failed: {e}")

    # 5. If pkl model is active, schedule a delayed initial risk score computation.
    #    We delay 60s to let the seed data settle, and only run if real data
    #    (sentiment scores / GDELT events) is available — otherwise the LR model
    #    saturates at 100 due to no input signal.
    if settings.model_backend == "pickle":
        try:
            import threading
            def _initial_risk_run():
                import time
                time.sleep(60)  # wait for scheduler to collect some data first
                from database import get_db_session
                from models.sentiment_score import SentimentScore as SS
                from models.gdelt_event import GdeltEvent as GE
                with get_db_session() as db:
                    has_sentiment = db.query(SS).count() > 0
                    has_gdelt = db.query(GE).count() > 0
                # Only run if we have real signal data — not just seed data
                if has_sentiment and has_gdelt:
                    from scoring.risk_calculator import RiskScoreEngine
                    logger.info("Running initial pkl model risk score computation (real data available)...")
                    n = RiskScoreEngine().run()
                    logger.info(f"Initial risk computation complete: {n} pairs scored by pkl model.")
                else:
                    logger.info(
                        "Skipping initial pkl model run — no real sentiment/GDELT data yet. "
                        "Seeded scores will display until the scheduler collects live data."
                    )
            threading.Thread(target=_initial_risk_run, daemon=True).start()
        except Exception as e:
            logger.error(f"Initial risk run failed: {e}")

    # 5. Start background scheduler
    if settings.enable_scheduler:
        try:
            from scheduler import start_scheduler
            start_scheduler()
        except Exception as e:
            logger.error(f"Scheduler failed to start: {e}")

    logger.info("GeoRisk Intelligence ready.")
    yield

    # Shutdown
    if settings.enable_scheduler:
        try:
            from scheduler import shutdown_scheduler
            shutdown_scheduler()
        except Exception:
            pass
    logger.info("GeoRisk Intelligence shut down.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="GeoRisk Intelligence API",
    description=(
        "Institutional-grade geopolitical risk intelligence platform. "
        "Provides real-time risk scores, bilateral analysis, market signals, "
        "and AI-generated intelligence briefs."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from routes import dashboard, bilateral, entities, briefs, alerts  # noqa: E402
from routes import markets, jobs, model as model_router, news       # noqa: E402
from routes import ingest as ingest_router                          # noqa: E402

# Core data endpoints
app.include_router(dashboard.router,      prefix="/api", tags=["Dashboard"])
app.include_router(bilateral.router,      prefix="/api", tags=["Bilateral"])
app.include_router(entities.router,       prefix="/api", tags=["Entities"])
app.include_router(briefs.router,         prefix="/api", tags=["Briefs"])
app.include_router(alerts.router,         prefix="/api", tags=["Alerts"])
app.include_router(markets.router,        prefix="/api", tags=["Markets"])
app.include_router(news.router,           prefix="/api", tags=["News"])

# Admin / ops endpoints
app.include_router(jobs.router,           prefix="/api", tags=["Jobs"])
app.include_router(model_router.router,   prefix="/api", tags=["Model"])

# Ingestion endpoints
app.include_router(ingest_router.router,  prefix="/api", tags=["Ingestion"])


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "service": "georisk-intelligence",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/system/status", tags=["Health"])
def system_status():
    """Detailed system status for monitoring."""
    from database import engine
    db_ok = True
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    scheduler_ok = False
    try:
        from scheduler import _scheduler
        scheduler_ok = _scheduler is not None and _scheduler.running
    except Exception:
        pass

    from services.model_service import get_model_service
    model_svc = get_model_service()

    return {
        "status": "operational" if db_ok else "degraded",
        "components": {
            "database": "ok" if db_ok else "error",
            "scheduler": "running" if scheduler_ok else "stopped",
            "model_service": type(model_svc).__name__,
            "model_ready": model_svc.is_ready(),
        },
        "config": {
            "model_backend": settings.model_backend,
            "enable_reddit": settings.enable_reddit,
            "enable_twitter": settings.enable_twitter,
            "enable_gdelt": settings.enable_gdelt,
            "enable_markets": settings.enable_markets,
        },
        "checked_at": datetime.utcnow().isoformat(),
    }


# ── Seed helper ───────────────────────────────────────────────────────────────
def _seed_reference_data():
    """Seed countries and politicians from JSON files. Idempotent."""
    from models.country import Country
    from models.politician import Politician

    data_dir = os.path.join(os.path.dirname(__file__), "data")

    countries_path = os.path.join(data_dir, "countries.json")
    if os.path.exists(countries_path):
        with open(countries_path) as f:
            countries = json.load(f)
        with get_db_session() as db:
            added = 0
            for c in countries:
                if not db.query(Country).filter_by(code=c["code"]).first():
                    db.add(Country(**c))
                    added += 1
        if added:
            logger.info(f"Countries seeded: {added} new records")

    politicians_path = os.path.join(data_dir, "politicians.json")
    if os.path.exists(politicians_path):
        with open(politicians_path) as f:
            politicians = json.load(f)
        with get_db_session() as db:
            added = 0
            for p in politicians:
                if not db.query(Politician).filter_by(
                    twitter_handle=p["twitter_handle"]
                ).first():
                    db.add(Politician(**p))
                    added += 1
        if added:
            logger.info(f"Politicians seeded: {added} new records")
