"""
models/risk_score.py — Final computed risk score per country-pair.
One row = one country-pair + one timestamp.
This is the core output of the entire pipeline.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from datetime import datetime
from database import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id                      = Column(Integer, primary_key=True, autoincrement=True)

    # Country pair (always stored alphabetically: "CN-US" not "US-CN")
    country_a               = Column(String(2), nullable=False, index=True)
    country_b               = Column(String(2), nullable=False, index=True)
    pair_key                = Column(String(6), nullable=False, index=True)  # "CN-US"

    # ── Risk Score ────────────────────────────────────────────────────────────
    score                   = Column(Float, nullable=False)     # 0–100
    classification          = Column(String(20))                # "LOW" | "MODERATE" | "HIGH" | "CRITICAL"

    # ── Component Scores (for breakdown display) ──────────────────────────────
    negative_sentiment_score        = Column(Float)             # 0–1
    sentiment_deterioration_rate    = Column(Float)             # 0–1
    politician_hostility_score      = Column(Float)             # 0–1
    gdelt_conflict_intensity        = Column(Float)             # 0–1
    vix_spike_score                 = Column(Float)             # 0–1
    market_stress_score             = Column(Float)             # 0–1

    # ── Input Data Window ─────────────────────────────────────────────────────
    # Explains what data was used
    window_hours            = Column(Integer, default=72)
    post_count_a            = Column(Integer, default=0)
    post_count_b            = Column(Integer, default=0)
    gdelt_event_count       = Column(Integer, default=0)

    # ── Contributing Factors ──────────────────────────────────────────────────
    # JSON array of top signals driving this score, for display
    # e.g. [{"factor": "Rising hostile rhetoric from @narendramodi", "impact": 0.18}, ...]
    contributing_factors    = Column(JSON, default=list)

    # Trend vs previous score
    prev_score              = Column(Float)                     # Score 72hrs ago
    score_change            = Column(Float)                     # Positive = worsening

    computed_at             = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return (
            f"<RiskScore {self.pair_key} = {self.score:.1f} "
            f"({self.classification}) @ {self.computed_at}>"
        )

    @staticmethod
    def classify(score: float) -> str:
        """
        Classify risk score into tiers based on geopolitical severity.
        
        Scoring model (as of May 22, 2026):
          0-20  → LOW (stable relations, no significant tensions)
          21-40 → MODERATE (some friction, manageable tensions)
          41-60 → HIGH (confrontation risk, elevated tensions)
          61-80 → CRITICAL (severe crisis potential)
          81-100 → CRITICAL (active war / near-war)
        """
        if score <= 20:
            return "LOW"
        elif score <= 40:
            return "MODERATE"
        elif score <= 60:
            return "HIGH"
        else:
            return "CRITICAL"

    @staticmethod
    def make_pair_key(a: str, b: str) -> str:
        """Always store pairs in alphabetical order."""
        return "-".join(sorted([a.upper(), b.upper()]))

