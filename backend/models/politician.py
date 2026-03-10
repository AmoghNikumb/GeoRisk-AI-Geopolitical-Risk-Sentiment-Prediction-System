"""
models/politician.py — Tracked politicians / public figures.
Seeded from data/politicians.json.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Politician(Base):
    __tablename__ = "politicians"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    twitter_handle  = Column(String(100), unique=True, nullable=False)  # "@narendramodi"
    name            = Column(String(200), nullable=False)               # "Narendra Modi"
    title           = Column(String(200))                               # "Prime Minister of India"
    country_code    = Column(String(2), ForeignKey("countries.code"))

    # Credibility / influence weighting (used in sentiment scoring)
    # Head of state = 1.0, Minister = 0.7, MP = 0.4, Influencer = 0.2
    influence_weight = Column(Float, default=0.5)

    is_verified     = Column(Boolean, default=True)
    is_active       = Column(Boolean, default=True)   # Set False to stop tracking
    created_at      = Column(DateTime, default=datetime.utcnow)
    last_scraped_at = Column(DateTime, nullable=True)

    # Relationships
    country = relationship("Country", back_populates="politicians")

    def __repr__(self):
        return f"<Politician {self.twitter_handle} — {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "twitter_handle": self.twitter_handle,
            "name": self.name,
            "title": self.title,
            "country_code": self.country_code,
            "influence_weight": self.influence_weight,
        }

