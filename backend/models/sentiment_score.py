"""
models/sentiment_score.py — Aggregated sentiment per country per hour.
Produced by aggregator.py after sentiment scoring.
One row = one country + one hour bucket.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    id                      = Column(Integer, primary_key=True, autoincrement=True)

    # Dimensions
    country_code            = Column(String(2), index=True)     # "IN"
    time_bucket             = Column(DateTime, index=True)       # 2024-01-15 14:00:00 (hour)

    # ── Aggregate Sentiment ───────────────────────────────────────────────────
    avg_sentiment           = Column(Float)                      # -1.0 to +1.0
    weighted_sentiment      = Column(Float)                      # Engagement-weighted average
    sentiment_delta         = Column(Float)                      # Change vs previous bucket

    # Source breakdowns
    politician_sentiment    = Column(Float)                      # Twitter verified accounts only
    public_sentiment        = Column(Float)                      # Reddit posts only
    twitter_sentiment       = Column(Float)                      # All Twitter posts
    reddit_sentiment        = Column(Float)                      # All Reddit posts

    # Volume signals
    post_count              = Column(Integer, default=0)         # Total posts in bucket
    twitter_count           = Column(Integer, default=0)
    reddit_count            = Column(Integer, default=0)
    post_volume_spike       = Column(Float, default=0.0)         # Z-score vs 7-day avg

    # Extremity signals
    negative_ratio          = Column(Float)                      # % of posts that are negative
    high_hostility_count    = Column(Integer, default=0)         # Posts scoring < -0.7

    computed_at             = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<SentimentScore {self.country_code} @ {self.time_bucket} "
            f"avg={self.avg_sentiment:.2f} n={self.post_count}>"
        )

