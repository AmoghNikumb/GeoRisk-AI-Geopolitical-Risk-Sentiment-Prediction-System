"""
scoring/risk_calculator.py
Computes the final 0–100 risk score for each country-pair.
Uses the weighted formula defined in the implementation doc.
"""
import logging
from datetime import datetime
from typing import List, Tuple, Dict

from database import get_db_session
from models.risk_score import RiskScore
from models.country import Country
from scoring.feature_builder import build_features
from config import settings

logger = logging.getLogger(__name__)

# ── Country pairs to monitor (alphabetical order) ────────────────────────────
TRACKED_PAIRS: List[Tuple[str, str]] = [
    ("CN", "US"),
    ("IN", "PK"),
    ("RU", "UA"),
    ("IL", "IR"),
    ("IN", "CN"),
    ("KP", "US"),
    ("KP", "KR"),
    ("IL", "SA"),
    ("RU", "GB"),
    ("CN", "TW"),
    ("TR", "GR"),
    ("IN", "US"),
]


def _normalize_sentiment_to_risk(sentiment: float) -> float:
    """
    Convert avg sentiment (-1 to +1) to a risk contribution (0 to 1).
    -1.0 (very hostile) → 1.0 risk
     0.0 (neutral)      → 0.5 risk
    +1.0 (very friendly)→ 0.0 risk
    """
    return round((1.0 - sentiment) / 2.0, 4)


def _normalize_vix(vix: float) -> float:
    """VIX: 0–15=low, 15–25=moderate, 25+= high. Map to 0–1."""
    return round(min(max((vix - 10) / 40.0, 0.0), 1.0), 4)


def _normalize_gdelt(event_count: int, min_goldstein: float) -> float:
    """
    Map GDELT signals to 0–1 conflict intensity.
    More events + lower Goldstein = higher score.
    """
    event_score    = min(event_count / 20.0, 1.0)
    goldstein_norm = min(abs(min_goldstein) / 10.0, 1.0) if min_goldstein < 0 else 0.0
    return round((event_score * 0.5 + goldstein_norm * 0.5), 4)


def _build_contributing_factors(features: Dict, component_scores: Dict) -> List[Dict]:
    """Build a human-readable list of top contributing factors for UI display."""
    factors = []

    if component_scores["negative_sentiment"] > 0.3:
        country_a = features["country_a"]
        country_b = features["country_b"]
        factors.append({
            "factor": f"High negative sentiment in {country_a}-{country_b} discourse",
            "impact": round(component_scores["negative_sentiment"] * settings.weight_negative_sentiment, 3),
            "category": "sentiment",
        })

    if component_scores["sentiment_deterioration"] > 0.2:
        factors.append({
            "factor": "Rapidly deteriorating rhetoric in last 72 hours",
            "impact": round(component_scores["sentiment_deterioration"] * settings.weight_sentiment_deterioration, 3),
            "category": "trend",
        })

    if component_scores["politician_hostility"] > 0.4:
        factors.append({
            "factor": "Hostile language from tracked political leaders",
            "impact": round(component_scores["politician_hostility"] * settings.weight_politician_hostility, 3),
            "category": "political",
        })

    if component_scores["gdelt_conflict"] > 0.3:
        factors.append({
            "factor": f"GDELT detected {features['gdelt_event_count']} conflict events in 72h window",
            "impact": round(component_scores["gdelt_conflict"] * settings.weight_gdelt_conflict, 3),
            "category": "events",
        })

    if component_scores["vix_spike"] > 0.4:
        factors.append({
            "factor": f"Elevated market fear index (VIX={features['vix']:.1f})",
            "impact": round(component_scores["vix_spike"] * settings.weight_vix_spike, 3),
            "category": "market",
        })

    if component_scores["market_stress"] > 0.4:
        factors.append({
            "factor": "Broad market stress signal (equity selloff + oil spike)",
            "impact": round(component_scores["market_stress"] * settings.weight_market_stress, 3),
            "category": "market",
        })

    # Sort by impact descending
    return sorted(factors, key=lambda x: x["impact"], reverse=True)


def compute_risk_score(country_a: str, country_b: str) -> RiskScore:
    """
    Main calculation function for a single country-pair.
    Returns an unsaved RiskScore object.
    """
    pair_key = RiskScore.make_pair_key(country_a, country_b)

    with get_db_session() as db:
        features = build_features(country_a, country_b, db)

        # ── Component Scores (all 0–1) ────────────────────────────────────────
        negative_sentiment = _normalize_sentiment_to_risk(
            features["combined_avg_sentiment"]
        )
        sentiment_deterioration = min(
            features["sentiment_deterioration_rate"], 1.0
        )
        politician_hostility = _normalize_sentiment_to_risk(
            features["combined_politician_hostility"]
        )
        gdelt_conflict = _normalize_gdelt(
            features["gdelt_event_count"], features["gdelt_min_goldstein"]
        )
        vix_spike   = _normalize_vix(features["vix"])
        market_stress = features["market_stress_score"]

        component_scores = {
            "negative_sentiment":    negative_sentiment,
            "sentiment_deterioration": sentiment_deterioration,
            "politician_hostility":  politician_hostility,
            "gdelt_conflict":        gdelt_conflict,
            "vix_spike":             vix_spike,
            "market_stress":         market_stress,
        }

        # ── Weighted Sum → 0–100 ──────────────────────────────────────────────
        raw_score = (
            settings.weight_negative_sentiment      * negative_sentiment +
            settings.weight_sentiment_deterioration * sentiment_deterioration +
            settings.weight_politician_hostility    * politician_hostility +
            settings.weight_gdelt_conflict          * gdelt_conflict +
            settings.weight_vix_spike               * vix_spike +
            settings.weight_market_stress           * market_stress
        ) * 100

        final_score = round(min(max(raw_score, 0.0), 100.0), 2)
        classification = RiskScore.classify(final_score)

        # Previous score for trend
        prev = db.query(RiskScore).filter_by(pair_key=pair_key).order_by(
            RiskScore.computed_at.desc()
        ).first()
        prev_score_val = prev.score if prev else None
        score_change = round(final_score - prev_score_val, 2) if prev_score_val is not None else 0.0

        contributing_factors = _build_contributing_factors(features, component_scores)

        risk = RiskScore(
            country_a=country_a.upper(),
            country_b=country_b.upper(),
            pair_key=pair_key,
            score=final_score,
            classification=classification,
            negative_sentiment_score=negative_sentiment,
            sentiment_deterioration_rate=sentiment_deterioration,
            politician_hostility_score=politician_hostility,
            gdelt_conflict_intensity=gdelt_conflict,
            vix_spike_score=vix_spike,
            market_stress_score=market_stress,
            window_hours=features["window_hours"],
            post_count_a=features["post_count_a"],
            post_count_b=features["post_count_b"],
            gdelt_event_count=features["gdelt_event_count"],
            contributing_factors=contributing_factors,
            prev_score=prev_score_val,
            score_change=score_change,
            computed_at=datetime.utcnow(),
        )

        db.add(risk)
        logger.info(
            f"Risk score {pair_key}: {final_score:.1f} ({classification}) "
            f"[Δ{score_change:+.1f}]"
        )

    return risk


class RiskScoreEngine:
    def run(self) -> int:
        """
        Main entry point — called by scheduler every hour.
        Computes risk scores for all tracked country pairs.
        """
        logger.info("Risk score engine starting...")
        computed = 0
        for a, b in TRACKED_PAIRS:
            try:
                compute_risk_score(a, b)
                computed += 1
            except Exception as e:
                logger.error(f"Risk score failed for {a}-{b}: {e}")
        logger.info(f"Risk engine done: {computed} pairs computed.")
        return computed

