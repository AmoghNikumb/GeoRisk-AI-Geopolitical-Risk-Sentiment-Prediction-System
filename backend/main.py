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

    # 4. Start background scheduler
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
