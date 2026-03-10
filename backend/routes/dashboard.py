"""
routes/dashboard.py — GET /api/dashboard
Returns: all country risk scores, top 5 high-risk pairs, latest market snapshot, unread alerts.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database import get_db
from models.risk_score import RiskScore
from models.market_snapshot import MarketSnapshot
from models.alert import Alert

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    # Latest risk score per pair
    subq = db.query(
        RiskScore.pair_key,
        func.max(RiskScore.computed_at).label("latest")
    ).group_by(RiskScore.pair_key).subquery()

    latest_scores = db.query(RiskScore).join(
        subq,
        (RiskScore.pair_key == subq.c.pair_key) &
        (RiskScore.computed_at == subq.c.latest)
    ).order_by(RiskScore.score.desc()).all()

    # Latest market snapshot
    market = db.query(MarketSnapshot).order_by(MarketSnapshot.captured_at.desc()).first()

    # Unread alerts (last 24h)
    alerts = db.query(Alert).filter(
        Alert.is_read == False,  # noqa: E712
        Alert.triggered_at >= datetime.utcnow() - timedelta(hours=24)
    ).order_by(Alert.triggered_at.desc()).all()

    return {
        "risk_scores": [
            {
                "pair_key": r.pair_key,
                "country_a": r.country_a,
                "country_b": r.country_b,
                "score": r.score,
                "classification": r.classification,
                "score_change": r.score_change,
                "computed_at": r.computed_at.isoformat() if r.computed_at else None,
            }
            for r in latest_scores
        ],
        "top_risks": [
            {
                "pair_key": r.pair_key,
                "country_a": r.country_a,
                "country_b": r.country_b,
                "score": r.score,
                "classification": r.classification,
                "headline_factors": [f["factor"] for f in (r.contributing_factors or [])[:2]],
            }
            for r in latest_scores[:5]
        ],
        "market": {
            "vix": market.vix if market else None,
            "sp500": market.sp500 if market else None,
            "sp500_change_pct": market.sp500_change_pct if market else None,
            "crude_oil": market.crude_oil if market else None,
            "gold": market.gold if market else None,
            "market_stress_score": market.market_stress_score if market else None,
            "captured_at": market.captured_at.isoformat() if market else None,
        } if market else None,
        "alerts": [
            {
                "id": a.id,
                "pair_key": a.pair_key,
                "title": a.title,
                "severity": a.severity,
                "triggered_at": a.triggered_at.isoformat(),
            }
            for a in alerts[:10]
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }

