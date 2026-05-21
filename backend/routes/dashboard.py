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

    # Unread alerts (last 7 days)
    alerts = db.query(Alert).filter(
        Alert.triggered_at >= datetime.utcnow() - timedelta(days=7)
    ).order_by(Alert.triggered_at.desc()).all()

    # Summary statistics
    total_pairs = len(latest_scores)
    critical_count = sum(1 for r in latest_scores if r.classification == "CRITICAL")
    high_count = sum(1 for r in latest_scores if r.classification == "HIGH")
    moderate_count = sum(1 for r in latest_scores if r.classification == "MODERATE")
    low_count = sum(1 for r in latest_scores if r.classification == "LOW")

    return {
        "summary": {
            "total_monitored_pairs": total_pairs,
            "critical_risk_pairs": critical_count,
            "high_risk_pairs": high_count,
            "moderate_risk_pairs": moderate_count,
            "low_risk_pairs": low_count,
            "unread_alerts": len([a for a in alerts if not a.is_read]),
            "last_update": datetime.utcnow().isoformat(),
        },
        "risk_scores": [
            {
                "pair_key": r.pair_key,
                "country_a": r.country_a,
                "country_b": r.country_b,
                "score": round(r.score, 2),
                "classification": r.classification,
                "score_change": round(r.score_change, 2) if r.score_change else None,
                "trend": "↑" if r.score_change and r.score_change > 0 else ("↓" if r.score_change and r.score_change < 0 else "→"),
                "prev_score": round(r.prev_score, 2) if r.prev_score else None,
                "contributing_factors": r.contributing_factors or [],
                "computed_at": r.computed_at.isoformat() if r.computed_at else None,
                "component_breakdown": {
                    "negative_sentiment": round(r.negative_sentiment_score or 0, 3),
                    "sentiment_deterioration": round(r.sentiment_deterioration_rate or 0, 3),
                    "politician_hostility": round(r.politician_hostility_score or 0, 3),
                    "gdelt_conflict": round(r.gdelt_conflict_intensity or 0, 3),
                    "vix_spike": round(r.vix_spike_score or 0, 3),
                    "market_stress": round(r.market_stress_score or 0, 3),
                },
                "data_quality": {
                    "posts_analyzed": r.post_count_a + r.post_count_b,
                    "gdelt_events": r.gdelt_event_count,
                    "confidence": min(1.0, (r.post_count_a + r.post_count_b) / 100.0),
                },
            }
            for r in latest_scores
        ],
        "top_risks": [
            {
                "pair_key": r.pair_key,
                "country_a": r.country_a,
                "country_b": r.country_b,
                "score": round(r.score, 2),
                "classification": r.classification,
                "headline_factors": [{"factor": f["factor"], "impact": f.get("impact", 0)} for f in (r.contributing_factors or [])[:3]],
                "spark_line": [],
            }
            for r in latest_scores[:8]
        ],
        "market": {
            "vix": round(market.vix, 2) if market and market.vix else None,
            "sp500": round(market.sp500, 2) if market and market.sp500 else None,
            "sp500_change_pct": round(market.sp500_change_pct, 3) if market and market.sp500_change_pct else None,
            "crude_oil": round(market.crude_oil, 2) if market and market.crude_oil else None,
            "gold": round(market.gold, 2) if market and market.gold else None,
            "dxy": round(market.dxy, 2) if market and market.dxy else None,
            "market_stress_score": round(market.market_stress_score, 3) if market and market.market_stress_score else None,
            "stress_level": (
                "CRITICAL" if market and market.market_stress_score and market.market_stress_score > 0.8
                else "HIGH" if market and market.market_stress_score and market.market_stress_score > 0.6
                else "MODERATE" if market and market.market_stress_score and market.market_stress_score > 0.4
                else "LOW"
            ) if market else "UNKNOWN",
            "captured_at": market.captured_at.isoformat() if market else None,
        },
        "alerts": [
            {
                "id": a.id,
                "pair_key": a.pair_key,
                "country_a": a.country_a,
                "country_b": a.country_b,
                "title": a.title,
                "message": a.message,
                "severity": a.severity,
                "score_delta": round(a.score_delta, 2) if a.score_delta else None,
                "alert_type": a.alert_type,
                "is_read": a.is_read,
                "triggered_at": a.triggered_at.isoformat(),
            }
            for a in alerts[:15]
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }

