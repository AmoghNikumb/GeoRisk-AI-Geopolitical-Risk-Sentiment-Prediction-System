"""
models/raw_post.py — Every scraped tweet / Reddit post in raw form.
This is the landing table — nothing is modified here.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class RawPost(Base):
    __tablename__ = "raw_posts"

    id              = Column(Integer, primary_key=True, autoincrement=True)

    # Source identification
    source          = Column(String(20), nullable=False)    # "twitter" | "reddit"
    post_id         = Column(String(200), unique=True, nullable=False)  # tweet_id / reddit post id
    url             = Column(String(500))

    # Content
    title           = Column(Text)                          # Reddit title / None for tweets
    body            = Column(Text, nullable=False)          # Full text
    author          = Column(String(200))                   # @handle or u/username
    author_verified = Column(Boolean, default=False)        # Verified account?

    # Engagement signals (used for weighting)
    upvotes         = Column(Integer, default=0)            # Reddit upvotes / Twitter likes
    retweet_count   = Column(Integer, default=0)
    reply_count     = Column(Integer, default=0)

    # Reddit-specific
    subreddit       = Column(String(100))                   # "worldnews", "geopolitics"

    # Twitter-specific
    politician_id   = Column(Integer, nullable=True)        # FK to politicians (if from tracked account)

    # Language detection (set during preprocessing)
    language        = Column(String(10))                    # "en", "hi", "ar", "ru", "zh"

    # Extracted entities (set during preprocessing)
    mentioned_countries = Column(JSON, default=list)        # ["US", "CN"]
    mentioned_persons   = Column(JSON, default=list)        # ["Biden", "Xi"]

    # Pipeline state flags
    processed       = Column(Boolean, default=False)        # Has been cleaned + entities extracted
    sentiment_scored = Column(Boolean, default=False)       # Has been scored by NLP model

    # Timestamps
    posted_at       = Column(DateTime)                      # Original post time
    scraped_at      = Column(DateTime, default=datetime.utcnow)

    # Relationship
    processed_post  = relationship("ProcessedPost", back_populates="raw_post", uselist=False)

    def __repr__(self):
        return f"<RawPost [{self.source}] {self.post_id[:20]}...>"

