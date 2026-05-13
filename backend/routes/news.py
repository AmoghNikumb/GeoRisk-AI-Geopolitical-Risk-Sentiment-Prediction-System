"""
routes/news.py — GET /api/geopolitical-news
Returns normalised geopolitical news items aggregated from public RSS feeds.
Results are cached server-side for 20 minutes.
"""
import logging
from fastapi import APIRouter, Query

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/geopolitical-news")
def get_geopolitical_news(
    region: str = Query(default="", description="Filter by region (e.g. Europe, Middle East)"),
    topic: str = Query(default="", description="Filter by topic (e.g. conflict, diplomacy)"),
    source: str = Query(default="", description="Filter by source_id"),
    limit: int = Query(default=60, ge=1, le=200),
    force_refresh: bool = Query(default=False, description="Bypass cache and re-fetch feeds"),
):
    from services.news_aggregator import fetch_news

    result = fetch_news(force=force_refresh)
    items = result["items"]

    # Apply filters
    if region:
        items = [i for i in items if i.get("region", "").lower() == region.lower()]
    if topic:
        items = [i for i in items if topic.lower() in [t.lower() for t in i.get("topics", [])]]
    if source:
        items = [i for i in items if i.get("source_id", "").lower() == source.lower()]

    return {
        "items": items[:limit],
        "total": len(items),
        "fetched_at": result["fetched_at"],
        "sources": result["sources"],
        "cached": result["cached"],
        "filters": {
            "region": region or None,
            "topic": topic or None,
            "source": source or None,
        },
    }
