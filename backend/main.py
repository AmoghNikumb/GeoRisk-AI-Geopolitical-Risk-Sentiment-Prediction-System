"""
main.py — GeoRisk AI FastAPI application.
Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
Docs at: http://localhost:8000/docs
"""
import logging
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db, get_db_session
from scheduler import start_scheduler, shutdown_scheduler

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan: startup + shutdown ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    logger.info("🌍 GeoRisk AI starting up...")
    # 1. Create DB tables
    init_db()
    # 2. Seed reference data
    _seed_reference_data()
    # 3. Start background scheduler
    start_scheduler()
    logger.info("✅ GeoRisk AI ready.")
    yield
    # Shutdown
    shutdown_scheduler()
    logger.info("GeoRisk AI shut down.")


app = FastAPI(
    title="GeoRisk AI",
    description="Geopolitical Risk Sentiment Prediction System",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow Next.js frontend on 3000) ─────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include Routers ───────────────────────────────────────────────────────────
from routes import dashboard, bilateral, entities, briefs, alerts  # noqa: E402

app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(bilateral.router, prefix="/api", tags=["Bilateral"])
app.include_router(entities.router,  prefix="/api", tags=["Entities"])
app.include_router(briefs.router,    prefix="/api", tags=["Briefs"])
app.include_router(alerts.router,    prefix="/api", tags=["Alerts"])


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "georisk-ai"}


# ── Seed Function ─────────────────────────────────────────────────────────────
def _seed_reference_data():
    """
    Seed countries and politicians tables from JSON files.
    Safe to call on every startup — skips existing rows.
    """
    from models.country import Country
    from models.politician import Politician

    data_dir = os.path.join(os.path.dirname(__file__), "data")

    # Seed countries
    countries_path = os.path.join(data_dir, "countries.json")
    if os.path.exists(countries_path):
        with open(countries_path) as f:
            countries = json.load(f)
        with get_db_session() as db:
            for c in countries:
                if not db.query(Country).filter_by(code=c["code"]).first():
                    db.add(Country(**c))
        logger.info(f"Countries seeded ({len(countries)} records)")

    # Seed politicians
    politicians_path = os.path.join(data_dir, "politicians.json")
    if os.path.exists(politicians_path):
        with open(politicians_path) as f:
            politicians = json.load(f)
        with get_db_session() as db:
            for p in politicians:
                if not db.query(Politician).filter_by(
                    twitter_handle=p["twitter_handle"]
                ).first():
                    db.add(Politician(**p))
        logger.info(f"Politicians seeded ({len(politicians)} records)")

