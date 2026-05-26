"""
scoring/risk_calculator.py
Computes the final 0–100 risk score for each country-pair.

When MODEL_BACKEND=pickle  → uses georisk_lr.pkl (LogisticRegression, 59 GDELT features)
When MODEL_BACKEND=dummy   → uses the rule-based weighted formula (always available)

Both paths produce the same RiskScore object — the rest of the system is unaffected.
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
    # CRITICAL
    ("IL", "IR"),
    ("US", "IR"),
    ("RU", "UA"),
    ("IL", "PS"),
    # HIGH
    ("US", "CN"),
    ("RU", "US"),
    ("KP", "KR"),
    ("IN", "PK"),
    # MODERATE
    ("GB", "US"),
    ("CN", "TW"),
    ("CN", "IN"),
    ("CN", "JP"),
    # LOW (kept for live scoring coverage)
    ("KP", "US"),
    ("IL", "SA"),
    ("TR", "GR"),
]

# ── Pinned scores — these override any ML model output ───────────────────────
# These are the authoritative geopolitical risk scores as of May 22, 2026.
# The ML model runs for component scores / contributing factors only.
# To change a score, update this dict and run update_risk_scores.py.
PINNED_SCORES: Dict[str, float] = {
    "IL-IR":  96.0,   # Israel-Iran: near-war, direct strikes exchanged
    "IR-US":  96.0,   # US-Iran: nuclear brinkmanship, maximum pressure
    "RU-UA":  95.0,   # Russia-Ukraine: active war
    "IL-PS":  88.0,   # Israel-Palestine: ongoing conflict, humanitarian crisis
    "CN-US":  74.0,   # US-China: trade war escalation, Taiwan flashpoint
    "RU-US":  69.0,   # Russia-US: proxy war, nuclear signalling, sanctions
    "KP-KR":  63.0,   # North Korea-South Korea: provocations, military posturing
    "IN-PK":  62.0,   # India-Pakistan: post-conflict ceasefire under strain
    "GB-US":  46.0,   # UK-US: trade friction, post-Brexit tensions
    "CN-TW":  51.0,   # China-Taiwan: cross-strait military pressure
    "CN-IN":  52.0,   # China-India: border standoffs, LAC friction
    "CN-JP":  38.0,   # China-Japan: East China Sea, Senkaku disputes
}


# ── Rule-based normalisers (used by dummy backend + contributing factors) ─────

def _normalize_sentiment_to_risk(sentiment: float) -> float:
    """Convert avg sentiment (-1 to +1) → risk contribution (0 to 1)."""
    return round((1.0 - sentiment) / 2.0, 4)


def _normalize_vix(vix: float) -> float:
    """VIX: 0–15=low, 15–25=moderate, 25+=high. Map to 0–1."""
    return round(min(max((vix - 10) / 40.0, 0.0), 1.0), 4)


def _normalize_gdelt(event_count: int, min_goldstein: float) -> float:
    """Map GDELT signals to 0–1 conflict intensity."""
    event_score    = min(event_count / 20.0, 1.0)
    goldstein_norm = min(abs(min_goldstein) / 10.0, 1.0) if min_goldstein < 0 else 0.0
    return round((event_score * 0.5 + goldstein_norm * 0.5), 4)


def _build_component_scores(features: Dict) -> Dict:
    """Compute the 6 normalised component scores (0–1) from raw features."""
    return {
        "negative_sentiment":      _normalize_sentiment_to_risk(features["combined_avg_sentiment"]),
        "sentiment_deterioration": min(features["sentiment_deterioration_rate"], 1.0),
        "politician_hostility":    _normalize_sentiment_to_risk(features["combined_politician_hostility"]),
        "gdelt_conflict":          _normalize_gdelt(features["gdelt_event_count"], features["gdelt_min_goldstein"]),
        "vix_spike":               _normalize_vix(features["vix"]),
        "market_stress":           features["market_stress_score"],
    }


def _rule_based_score(component_scores: Dict) -> float:
    """Weighted sum of component scores → 0–100."""
    raw = (
        settings.weight_negative_sentiment      * component_scores["negative_sentiment"] +
        settings.weight_sentiment_deterioration * component_scores["sentiment_deterioration"] +
        settings.weight_politician_hostility    * component_scores["politician_hostility"] +
        settings.weight_gdelt_conflict          * component_scores["gdelt_conflict"] +
        settings.weight_vix_spike               * component_scores["vix_spike"] +
        settings.weight_market_stress           * component_scores["market_stress"]
    ) * 100
    return round(min(max(raw, 0.0), 100.0), 2)


def _build_contributing_factors(features: Dict, component_scores: Dict) -> List[Dict]:
    """Build human-readable contributing factors for UI display."""
    factors = []

    if component_scores["negative_sentiment"] > 0.3:
        factors.append({
            "factor": f"High negative sentiment in {features['country_a']}-{features['country_b']} discourse",
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

    return sorted(factors, key=lambda x: x["impact"], reverse=True)


# ── Main calculation ──────────────────────────────────────────────────────────

def compute_risk_score(country_a: str, country_b: str) -> RiskScore:
    """
    Compute risk score for a single country-pair and persist it.

    Routing:
      MODEL_BACKEND=pickle → georisk_lr.pkl (LogisticRegression, 59 GDELT features)
      MODEL_BACKEND=dummy  → rule-based weighted formula

    Data quality guard:
      If the only available data is seeded demo sentiment (no real scraped posts),
      the LR model saturates at 0 or 100 due to insufficient signal variance.
      In that case, we preserve the existing seeded score and skip overwriting.
    """
    pair_key = RiskScore.make_pair_key(country_a, country_b)

    with get_db_session() as db:
        features = build_features(country_a, country_b, db)

        # ── Data quality check ────────────────────────────────────────────────
        # ProcessedPost rows only exist when real scrapers have run.
        # If none exist, we have only seeded demo data — the LR model will
        # saturate at 0/100 with no real signal variance. Preserve seeded scores.
        from models.processed_post import ProcessedPost
        has_real_scraped_data = db.query(ProcessedPost).count() > 0

        if not has_real_scraped_data and settings.model_backend == "pickle":
            existing = db.query(RiskScore).filter_by(pair_key=pair_key).order_by(
                RiskScore.computed_at.desc()
            ).first()
            if existing and existing.score > 0:
                logger.debug(
                    f"{pair_key}: no real scraped data yet — preserving seeded score "
                    f"{existing.score:.1f} ({existing.classification})"
                )
                return existing

        # Always compute component scores — used for contributing factors + fallback
        component_scores = _build_component_scores(features)

        # ── Score computation: pkl model or rule-based ────────────────────────
        if settings.model_backend == "pickle":
            try:
                from services.model_service import get_model_service
                svc = get_model_service()
                if svc.is_ready():
                    result = svc.predict(features)
                    final_score = result["predicted_score"]
                    model_used  = "pickle"
                    logger.debug(
                        f"{pair_key}: pkl model → {final_score:.1f} "
                        f"(conf={result['confidence']:.3f})"
                    )
                else:
                    logger.warning(f"{pair_key}: pkl model not ready, falling back to rule-based")
                    final_score = _rule_based_score(component_scores)
                    model_used  = "dummy_fallback"
            except Exception as e:
                logger.error(f"{pair_key}: pkl model error ({e}), falling back to rule-based")
                final_score = _rule_based_score(component_scores)
                model_used  = "dummy_fallback"
        else:
            final_score = _rule_based_score(component_scores)
            model_used  = "dummy"

        classification = RiskScore.classify(final_score)

        # ── Pinned score override ─────────────────────────────────────────────
        # If this pair has a pinned score, use it regardless of model output.
        # Component scores and contributing factors are still computed from
        # real data for the breakdown panel — only the headline score is pinned.
        if pair_key in PINNED_SCORES:
            pinned = PINNED_SCORES[pair_key]
            if abs(final_score - pinned) > 0.5:
                logger.info(
                    f"{pair_key}: model score {final_score:.1f} overridden by "
                    f"pinned score {pinned:.1f}"
                )
            final_score = pinned
            classification = RiskScore.classify(final_score)

        # Previous score for trend delta
        prev = db.query(RiskScore).filter_by(pair_key=pair_key).order_by(
            RiskScore.computed_at.desc()
        ).first()
        prev_score_val = prev.score if prev else None
        score_change   = round(final_score - prev_score_val, 2) if prev_score_val is not None else 0.0

        contributing_factors = _build_contributing_factors(features, component_scores)

        risk = RiskScore(
            country_a=country_a.upper(),
            country_b=country_b.upper(),
            pair_key=pair_key,
            score=final_score,
            classification=classification,
            negative_sentiment_score=component_scores["negative_sentiment"],
            sentiment_deterioration_rate=component_scores["sentiment_deterioration"],
            politician_hostility_score=component_scores["politician_hostility"],
            gdelt_conflict_intensity=component_scores["gdelt_conflict"],
            vix_spike_score=component_scores["vix_spike"],
            market_stress_score=component_scores["market_stress"],
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
            f"[Δ{score_change:+.1f}] [model={model_used}]"
        )

    return risk


class RiskScoreEngine:
    def run(self) -> int:
        """
        Main entry point — called by scheduler every hour.
        Computes risk scores for all tracked country pairs.

        Guard: if no real scraped data (ProcessedPost) exists yet,
        skip the run entirely to preserve seeded scores.
        The LR model saturates at 0/100 with only seeded sentiment data.
        """
        # Check for real scraped data before running
        from models.processed_post import ProcessedPost
        with get_db_session() as db:
            has_real_data = db.query(ProcessedPost).count() > 0

        if not has_real_data:
            logger.info(
                "Risk engine skipped — no real scraped posts yet. "
                "Seeded scores preserved. Engine will activate once "
                "Twitter/Reddit collectors have run."
            )
            return 0

        logger.info(
            f"Risk score engine starting "
            f"[backend={settings.model_backend}] ..."
        )
        computed = 0
        for a, b in TRACKED_PAIRS:
            try:
                compute_risk_score(a, b)
                computed += 1
            except Exception as e:
                logger.error(f"Risk score failed for {a}-{b}: {e}")
        logger.info(f"Risk engine done: {computed}/{len(TRACKED_PAIRS)} pairs computed.")
        return computed
