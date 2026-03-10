"""routes/entities.py — GET /api/entities?country=US"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db
from models.politician import Politician
from models.processed_post import ProcessedPost

router = APIRouter()


@router.get("/entities")
def get_entities(
    country: str = Query(..., min_length=2, max_length=2),
    db: Session = Depends(get_db),
):
    country = country.upper()
    since = datetime.utcnow() - timedelta(hours=72)

    politicians = db.query(Politician).filter_by(
        country_code=country, is_active=True
    ).all()

    pol_data = []
    for pol in politicians:
        recent_posts = db.query(ProcessedPost).filter(
            ProcessedPost.author == pol.twitter_handle,
            ProcessedPost.posted_at >= since,
            ProcessedPost.sentiment_scored == True,  # noqa: E712
        ).order_by(ProcessedPost.posted_at.desc()).limit(10).all()

        avg_sent = (
            sum(p.sentiment_score for p in recent_posts if p.sentiment_score is not None)
            / len([p for p in recent_posts if p.sentiment_score is not None])
        ) if recent_posts else None

        pol_data.append({
            "id": pol.id,
            "name": pol.name,
            "twitter_handle": pol.twitter_handle,
            "title": pol.title,
            "influence_weight": pol.influence_weight,
            "avg_sentiment_72h": round(avg_sent, 4) if avg_sent is not None else None,
            "recent_posts": [
                {
                    "text": p.clean_text[:200],
                    "sentiment_score": p.sentiment_score,
                    "sentiment_label": p.sentiment_label,
                    "posted_at": p.posted_at.isoformat() if p.posted_at else None,
                }
                for p in recent_posts[:5]
            ],
        })

    # Most inflammatory posts from this country
    inflammatory = db.query(ProcessedPost).filter(
        ProcessedPost.mentioned_countries.contains([country]),
        ProcessedPost.sentiment_score < -0.5,
        ProcessedPost.posted_at >= since,
    ).order_by(ProcessedPost.sentiment_score.asc()).limit(20).all()

    return {
        "country": country,
        "politicians": pol_data,
        "inflammatory_posts": [
            {
                "source": p.source,
                "author": p.author,
                "text": p.clean_text[:300],
                "sentiment_score": p.sentiment_score,
                "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            }
            for p in inflammatory
        ],
    }

