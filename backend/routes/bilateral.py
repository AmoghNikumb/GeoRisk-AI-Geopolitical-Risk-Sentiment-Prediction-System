"""
routes/bilateral.py — GET /api/bilateral?a=US&b=CN
Returns: 72hr sentiment timeline, risk score breakdown, top posts, intel brief, GDELT events.
"""
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db
from models.risk_score import RiskScore
from models.sentiment_score import SentimentScore
from models.processed_post import ProcessedPost
from models.intel_brief import IntelBrief
from models.gdelt_event import GdeltEvent

router = APIRouter()


@router.get("/bilateral")
def get_bilateral(
    a: str = Query(..., min_length=2, max_length=2),
    b: str = Query(..., min_length=2, max_length=2),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    a, b = a.upper(), b.upper()
    pair_key = RiskScore.make_pair_key(a, b)
    since_72h = datetime.utcnow() - timedelta(hours=72)

    # Latest risk score
    risk = db.query(RiskScore).filter_by(pair_key=pair_key).order_by(
        RiskScore.computed_at.desc()
    ).first()

    # Sentiment timeline (last 72h, both countries)
    def get_timeline(country_code):
        rows = db.query(SentimentScore).filter(
            SentimentScore.country_code == country_code,
            SentimentScore.time_bucket >= since_72h,
        ).order_by(SentimentScore.time_bucket.asc()).all()
        return [
            {
                "time": r.time_bucket.isoformat(),
                "avg": r.avg_sentiment,
                "politician": r.politician_sentiment,
                "public": r.public_sentiment,
                "count": r.post_count,
            }
            for r in rows
        ]

    # Top driving posts
    top_posts = db.query(ProcessedPost).filter(
        ProcessedPost.posted_at >= since_72h,
        ProcessedPost.sentiment_score < -0.2,
    ).filter(
        ProcessedPost.mentioned_countries.contains([a]) |
        ProcessedPost.mentioned_countries.contains([b])
    ).order_by(ProcessedPost.sentiment_score.asc()).limit(20).all()

    # Latest intel brief
    brief = db.query(IntelBrief).filter_by(pair_key=pair_key).order_by(
        IntelBrief.generated_at.desc()
    ).first()

    # If no brief or expired — trigger background generation
    if brief is None or brief.is_expired():
        if background_tasks:
            background_tasks.add_task(_generate_brief_bg, a, b)

    # GDELT events
    gdelt = db.query(GdeltEvent).filter(
        GdeltEvent.event_date >= since_72h,
        GdeltEvent.goldstein_scale < -5,
    ).filter(
        (GdeltEvent.actor1_country.in_([a, b])) |
        (GdeltEvent.actor2_country.in_([a, b]))
    ).order_by(GdeltEvent.goldstein_scale.asc()).limit(20).all()

    return {
        "pair_key": pair_key,
        "country_a": a,
        "country_b": b,
        "risk_score": {
            "score": risk.score if risk else None,
            "classification": risk.classification if risk else "UNKNOWN",
            "score_change": risk.score_change if risk else None,
            "contributing_factors": risk.contributing_factors if risk else [],
            "breakdown": {
                "negative_sentiment": risk.negative_sentiment_score if risk else None,
                "sentiment_deterioration": risk.sentiment_deterioration_rate if risk else None,
                "politician_hostility": risk.politician_hostility_score if risk else None,
                "gdelt_conflict": risk.gdelt_conflict_intensity if risk else None,
                "vix_spike": risk.vix_spike_score if risk else None,
                "market_stress": risk.market_stress_score if risk else None,
            },
            "computed_at": risk.computed_at.isoformat() if risk else None,
        },
        "sentiment_timeline": {
            "country_a": get_timeline(a),
            "country_b": get_timeline(b),
        },
        "top_posts": [
            {
                "source": p.source,
                "author": p.author,
                "text": p.clean_text[:300],
                "sentiment_score": p.sentiment_score,
                "sentiment_label": p.sentiment_label,
                "posted_at": p.posted_at.isoformat() if p.posted_at else None,
                "is_politician": p.author_verified,
            }
            for p in top_posts
        ],
        "intel_brief": {
            "headline": brief.headline if brief else None,
            "risk_level": brief.risk_level if brief else None,
            "summary": brief.summary if brief else None,
            "key_drivers": brief.key_drivers if brief else [],
            "market_implications": brief.market_implications if brief else None,
            "outlook_72hr": brief.outlook_72hr if brief else None,
            "confidence": brief.confidence if brief else None,
            "generated_at": brief.generated_at.isoformat() if brief else None,
            "is_generating": brief is None or brief.is_expired(),
        },
        "gdelt_events": [
            {
                "actor1": e.actor1_country,
                "actor2": e.actor2_country,
                "event_code": e.event_code,
                "goldstein_scale": e.goldstein_scale,
                "num_articles": e.num_articles,
                "event_date": e.event_date.isoformat() if e.event_date else None,
                "geo": e.action_geo_name,
            }
            for e in gdelt
        ],
    }


def _generate_brief_bg(country_a: str, country_b: str):
    """Background task to generate brief without blocking the response."""
    try:
        from llm.brief_generator import BriefGenerator
        BriefGenerator().generate(country_a, country_b, trigger="on_demand")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Background brief gen failed: {e}")

