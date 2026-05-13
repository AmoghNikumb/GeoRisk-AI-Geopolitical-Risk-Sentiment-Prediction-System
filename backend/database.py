"""
database.py — SQLAlchemy engine, session factory, and base model.
Import `get_db` as a FastAPI dependency in all route handlers.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

from config import settings

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────
_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    **({} if _is_sqlite else dict(
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )),
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    echo=(settings.app_env == "development"),
)

# ── Session Factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ── Declarative Base ──────────────────────────────────────────────────────────
Base = declarative_base()


# ── FastAPI Dependency ────────────────────────────────────────────────────────
def get_db():
    """
    Yields a database session and ensures it is closed after the request.
    Usage in routes:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Context Manager (for non-FastAPI use — schedulers, scripts) ──────────────
@contextmanager
def get_db_session():
    """
    Context manager for use outside FastAPI (schedulers, collectors, etc).
    Usage:
        with get_db_session() as db:
            db.query(RawPost).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"DB session error: {e}")
        raise
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist. Called on app startup."""
    import models  # noqa: F401 — ensures all models are registered
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")


def check_db_connection() -> bool:
    """Health check — returns True if DB is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        return False

