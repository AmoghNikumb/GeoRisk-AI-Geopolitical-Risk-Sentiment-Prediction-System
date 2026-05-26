"""
routes/ingest.py — POST /api/ingest/apify

Accepts a JSON body with a ``file_path`` field (relative to the backend root
directory), runs the ApifyIngester pipeline, and returns an ingestion summary.

Concurrency guard: an in-memory set protected by a threading.Lock prevents
the same file from being ingested concurrently within the same process.
"""

from __future__ import annotations

import logging
import threading
import traceback
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from collectors.apify_ingester import ApifyIngester

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory concurrency guard
# ---------------------------------------------------------------------------
_active_jobs: set[str] = set()
_lock = threading.Lock()

# Backend root directory: routes/ is one level below backend/
_BACKEND_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    file_path: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/ingest/apify")
def ingest_apify(request: IngestRequest):
    """Ingest a pre-scraped Apify Twitter dataset file.

    The ``file_path`` is resolved relative to the backend root directory.
    Absolute paths and path traversal attempts (``..``) are rejected.

    Returns:
        HTTP 200 with an :class:`IngestionSummary` dict on success.

    Raises:
        HTTP 400: Path contains ``..`` (path traversal guard).
        HTTP 404: File does not exist on the server.
        HTTP 409: The same file is already being ingested.
        HTTP 422: ``file_path`` field is missing (handled by FastAPI/Pydantic).
        HTTP 500: Unhandled exception during ingestion.
    """
    # ------------------------------------------------------------------
    # 1. Path traversal guard
    # ------------------------------------------------------------------
    if ".." in request.file_path:
        raise HTTPException(status_code=400, detail="Invalid file path")

    # ------------------------------------------------------------------
    # 2. Resolve path relative to backend root
    # ------------------------------------------------------------------
    resolved_path = str((_BACKEND_ROOT / request.file_path).resolve())

    # ------------------------------------------------------------------
    # 3. File existence check
    # ------------------------------------------------------------------
    if not Path(resolved_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {request.file_path}",
        )

    # ------------------------------------------------------------------
    # 4. Concurrency guard — reject duplicate concurrent ingestion
    # ------------------------------------------------------------------
    with _lock:
        if resolved_path in _active_jobs:
            raise HTTPException(
                status_code=409,
                detail=f"Ingestion already running for: {request.file_path}",
            )
        _active_jobs.add(resolved_path)

    # ------------------------------------------------------------------
    # 5. Run ingestion
    # ------------------------------------------------------------------
    try:
        ingester = ApifyIngester()
        summary = ingester.ingest(Path(resolved_path))
        return summary.to_dict()
    except Exception as exc:
        logger.error(
            "Ingestion failed for %s:\n%s",
            request.file_path,
            traceback.format_exc(),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {exc}",
        )
    finally:
        with _lock:
            _active_jobs.discard(resolved_path)
