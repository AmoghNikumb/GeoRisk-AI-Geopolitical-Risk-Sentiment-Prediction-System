"""
models/intel_brief.py — LLM-generated intelligence reports.
Stored as structured JSON + full text for display.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey
from datetime import datetime
from database import Base


class IntelBrief(Base):
    __tablename__ = "intel_briefs"

    id              = Column(Integer, primary_key=True, autoincrement=True)

    # Country pair
    country_a       = Column(String(2), nullable=False, index=True)
    country_b       = Column(String(2), nullable=False, index=True)
    pair_key        = Column(String(6), nullable=False, index=True)

    # Risk context at time of generation
    risk_score_id   = Column(Integer, ForeignKey("risk_scores.id"))
    risk_score_val  = Column(Float)
    risk_level      = Column(String(20))                # "HIGH"

    # ── LLM Output (structured JSON) ──────────────────────────────────────────
    headline        = Column(Text)                      # One-line summary
    summary         = Column(Text)                      # 2–3 paragraph analysis
    key_drivers     = Column(JSON, default=list)        # List of driving factors
    market_implications = Column(Text)                  # Financial impact analysis
    outlook_72hr    = Column(Text)                      # Near-term prediction
    confidence      = Column(Float)                     # 0.0–1.0

    # Raw LLM response stored for debugging
    raw_response    = Column(JSON)

    # Trigger type
    trigger         = Column(String(50))                # "on_demand" | "scheduled" | "threshold"

    # Cache control
    generated_at    = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at      = Column(DateTime)                  # Don't regenerate before this

    def __repr__(self):
        return f"<IntelBrief {self.pair_key} | {self.risk_level} @ {self.generated_at}>"

    def is_expired(self) -> bool:
        return self.expires_at and datetime.utcnow() > self.expires_at

