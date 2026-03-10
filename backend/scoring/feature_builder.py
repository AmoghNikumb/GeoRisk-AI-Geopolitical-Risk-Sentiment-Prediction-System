"""
scoring/feature_builder.py
Assembles the feature vector for a country-pair from the last 72 hours.
These features feed directly into risk_calculator.py.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List

from sqlalchemy.orm import Session

from models.sentiment_score import SentimentScore
from models.market_snapshot import MarketSnapshot
from models.gdelt_event import GdeltEvent

logger = logging.getLogger(__name__)

WINDOW_HOURS = 72


def build_features(country_a: str, country_b: str, db: Session) -> Dict:
    """
    Build the full feature vector for a country-pair.
    Returns a dict of all signals used in risk calculation.
    """
    now = datetime.utcnow()
    since = now - timedelta(hours=WINDOW_HOURS)

    features = {
        "country_a": country_a,
        "country_b": country_b,
        "window_hours": WINDOW_HOURS,
        "computed_at": now,
    }

    # ── Sentiment Features ────────────────────────────────────────────────────
    for country, key in [(country_a, "a"), (country_b, "b")]:
        rows = db.query(SentimentScore).filter(
            SentimentScore.country_code == country,
            SentimentScore.time_bucket >= since,
        ).order_by(SentimentScore.time_bucket.desc()).all()

        if rows:
            # Use most recent bucket's sentiment
            latest = rows[0]
            # Average over window for robustness
            avg_window = sum(r.avg_sentiment or 0 for r in rows) / len(rows)
            features[f"avg_sentiment_{key}"]         = avg_window
            features[f"latest_sentiment_{key}"]      = latest.avg_sentiment or 0
            features[f"politician_sentiment_{key}"]  = latest.politician_sentiment or avg_window
            features[f"public_sentiment_{key}"]      = latest.public_sentiment or avg_window
            features[f"post_count_{key}"]            = sum(r.post_count for r in rows)
            features[f"negative_ratio_{key}"]        = latest.negative_ratio or 0
            features[f"high_hostility_{key}"]        = latest.high_hostility_count or 0
            features[f"volume_spike_{key}"]          = latest.post_volume_spike or 0

            # Deterioration rate: how much has sentiment worsened?
            if len(rows) >= 2:
                oldest_avg = rows[-1].avg_sentiment or 0
                newest_avg = rows[0].avg_sentiment or 0
                features[f"sentiment_delta_{key}"] = newest_avg - oldest_avg
            else:
                features[f"sentiment_delta_{key}"] = 0.0
        else:
            # No data — neutral defaults
            features[f"avg_sentiment_{key}"]         = 0.0
            features[f"latest_sentiment_{key}"]      = 0.0
            features[f"politician_sentiment_{key}"]  = 0.0
            features[f"public_sentiment_{key}"]      = 0.0
            features[f"post_count_{key}"]            = 0
            features[f"negative_ratio_{key}"]        = 0.0
            features[f"high_hostility_{key}"]        = 0
            features[f"volume_spike_{key}"]          = 0.0
            features[f"sentiment_delta_{key}"]       = 0.0

    # ── Combined Sentiment Signals ────────────────────────────────────────────
    features["combined_avg_sentiment"] = (
        features["avg_sentiment_a"] + features["avg_sentiment_b"]
    ) / 2

    features["combined_politician_hostility"] = (
        features["politician_sentiment_a"] + features["politician_sentiment_b"]
    ) / 2

    features["sentiment_deterioration_rate"] = min(
        abs(features["sentiment_delta_a"]) + abs(features["sentiment_delta_b"]), 1.0
    ) / 2

    # ── GDELT Features ────────────────────────────────────────────────────────
    gdelt_rows = db.query(GdeltEvent).filter(
        GdeltEvent.event_date >= since,
        GdeltEvent.goldstein_scale < -5,
    ).filter(
        # Events involving either country
        (GdeltEvent.actor1_country.in_([country_a, country_b])) |
        (GdeltEvent.actor2_country.in_([country_a, country_b])) |
        (GdeltEvent.action_country.in_([country_a, country_b]))
    ).all()

    features["gdelt_event_count"]        = len(gdelt_rows)
    features["gdelt_avg_tone"]           = (
        sum(e.avg_tone or 0 for e in gdelt_rows) / len(gdelt_rows)
        if gdelt_rows else 0.0
    )
    features["gdelt_min_goldstein"]      = (
        min(e.goldstein_scale for e in gdelt_rows) if gdelt_rows else 0.0
    )
    features["gdelt_total_articles"]     = sum(e.num_articles or 0 for e in gdelt_rows)

    # ── Market Features ───────────────────────────────────────────────────────
    latest_market = db.query(MarketSnapshot).order_by(
        MarketSnapshot.captured_at.desc()
    ).first()

    if latest_market:
        features["vix"]                  = latest_market.vix or 15.0
        features["market_stress_score"]  = latest_market.market_stress_score or 0.0
        features["sp500_change_pct"]     = latest_market.sp500_change_pct or 0.0
    else:
        features["vix"]                  = 15.0
        features["market_stress_score"]  = 0.0
        features["sp500_change_pct"]     = 0.0

    return features

