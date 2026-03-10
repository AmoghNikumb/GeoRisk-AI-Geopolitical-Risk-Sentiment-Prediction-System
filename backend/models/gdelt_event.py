"""
models/gdelt_event.py — Conflict events pulled from the GDELT Project API.
Used as a ground-truth signal and for validation labels.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from database import Base


class GdeltEvent(Base):
    __tablename__ = "gdelt_events"

    id                  = Column(Integer, primary_key=True, autoincrement=True)

    # GDELT event identification
    gdelt_event_id      = Column(String(50), unique=True)
    event_date          = Column(DateTime, index=True)

    # Actors
    actor1_country      = Column(String(10), index=True)   # ISO code: "US"
    actor2_country      = Column(String(10), index=True)   # ISO code: "CN"
    actor1_name         = Column(String(200))
    actor2_name         = Column(String(200))

    # GDELT Event Classification
    event_code          = Column(String(10))               # CAMEO event code
    event_description   = Column(Text)                     # Human-readable description

    # ── GoldsteinScale ────────────────────────────────────────────────────────
    # -10 (most destabilizing) to +10 (most stabilizing)
    # We filter for < -5 as "high conflict events"
    goldstein_scale     = Column(Float, index=True)

    # Volume/prominence signal
    num_articles        = Column(Integer, default=0)       # Number of news articles covering this
    num_sources         = Column(Integer, default=0)
    avg_tone            = Column(Float)                    # GDELT avg tone of coverage

    # Location
    action_country      = Column(String(10))
    action_geo_name     = Column(String(200))
    action_lat          = Column(Float)
    action_long         = Column(Float)

    fetched_at          = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<GdeltEvent {self.actor1_country}→{self.actor2_country} "
            f"GS={self.goldstein_scale} on {self.event_date}>"
        )

