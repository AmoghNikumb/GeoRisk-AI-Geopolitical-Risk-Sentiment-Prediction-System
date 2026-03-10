"""
models/alert.py — Triggered alerts when risk spikes above threshold.
Polled by the frontend every 5 minutes.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from datetime import datetime
from database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id              = Column(Integer, primary_key=True, autoincrement=True)

    # Country pair
    country_a       = Column(String(2), nullable=False, index=True)
    country_b       = Column(String(2), nullable=False, index=True)
    pair_key        = Column(String(6), nullable=False, index=True)

    # Alert content
    alert_type      = Column(String(50))    # "score_jump" | "tier_change" | "critical_threshold"
    title           = Column(String(300))   # "⚠️ Risk jumped 22 points for US-CN"
    message         = Column(Text)          # Detailed description

    # Score context
    prev_score      = Column(Float)
    new_score       = Column(Float)
    score_delta     = Column(Float)
    new_classification = Column(String(20)) # "HIGH"

    # Severity
    severity        = Column(String(20))    # "INFO" | "WARNING" | "CRITICAL"

    # State
    is_read         = Column(Boolean, default=False)
    triggered_at    = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Alert [{self.severity}] {self.pair_key} +{self.score_delta:.1f} @ {self.triggered_at}>"

