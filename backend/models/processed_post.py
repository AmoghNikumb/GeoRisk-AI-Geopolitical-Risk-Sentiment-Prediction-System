"""
models/processed_post.py — Cleaned text + NLP scores.
Each row corresponds to one RawPost after the preprocessing pipeline.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class ProcessedPost(Base):
    __tablename__ = "processed_posts"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    raw_post_id     = Column(Integer, ForeignKey("raw_posts.id"), unique=True, nullable=False)

    # Cleaned content
    clean_text      = Column(Text, nullable=False)       # URL/HTML stripped, normalized

    # Language
    language        = Column(String(10))                 # "en", "ar", "hi", "ru", "zh"
    is_english      = Column(Boolean, default=True)

    # Extracted entities
    mentioned_countries = Column(JSON, default=list)     # ["IN", "PK"]
    mentioned_persons   = Column(JSON, default=list)     # ["Modi", "Sharif"]

    # Source metadata (denormalized for fast querying)
    source          = Column(String(20))                 # "twitter" | "reddit"
    author          = Column(String(200))
    author_verified = Column(Boolean, default=False)
    influence_weight = Column(Float, default=1.0)        # Politician weight or 1.0
    engagement_score = Column(Float, default=0.0)        # Normalized upvotes/likes
    politician_id   = Column(Integer, nullable=True)

    # ── NLP Sentiment Scores ──────────────────────────────────────────────────
    # Raw model output
    sentiment_label  = Column(String(20))                # "POSITIVE" | "NEUTRAL" | "NEGATIVE"
    sentiment_score  = Column(Float)                     # Normalized: -1.0 (very negative) → +1.0 (very positive)
    sentiment_confidence = Column(Float)                 # Model confidence 0.0–1.0

    # Model used
    sentiment_model  = Column(String(100))               # e.g. "cardiffnlp/twitter-roberta-base-sentiment"

    # Pipeline state
    sentiment_scored = Column(Boolean, default=False)

    # Timestamps
    posted_at        = Column(DateTime)
    processed_at     = Column(DateTime, default=datetime.utcnow)

    # Time bucket for aggregation (truncated to the hour)
    time_bucket      = Column(DateTime)                  # e.g. 2024-01-15 14:00:00

    # Relationship
    raw_post = relationship("RawPost", back_populates="processed_post")

    def __repr__(self):
        return f"<ProcessedPost {self.id} | {self.sentiment_label} {self.sentiment_score:.2f}>"

