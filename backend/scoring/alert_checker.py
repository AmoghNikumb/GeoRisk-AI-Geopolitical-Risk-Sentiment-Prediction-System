"""
scoring/alert_checker.py
Checks for significant risk score changes and creates alerts.
Runs every 15 minutes via APScheduler.
"""
import logging
from datetime import datetime, timedelta
from typing import List

from database import get_db_session
from models.risk_score import RiskScore
from models.alert import Alert
from config import settings

logger = logging.getLogger(__name__)

SEVERITY_MAP = {
    "LOW":      "INFO",
    "MODERATE": "WARNING",
    "HIGH":     "WARNING",
    "CRITICAL": "CRITICAL",
}


def _check_pair(pair_key: str, db) -> List[Alert]:
    """Check if a country-pair needs an alert. Returns list of Alert objects."""
    alerts = []

    # Get last 2 scores for this pair
    recent = db.query(RiskScore).filter_by(pair_key=pair_key).order_by(
        RiskScore.computed_at.desc()
    ).limit(2).all()

    if len(recent) < 2:
        return []

    latest, prev = recent[0], recent[1]
    delta = latest.score - prev.score
    time_diff_hours = (latest.computed_at - prev.computed_at).total_seconds() / 3600

    # ── Alert Condition 1: Score jumped > 15 points ───────────────────────────
    if delta >= settings.alert_score_jump:
        # Check we haven't already alerted for this exact spike
        existing = db.query(Alert).filter(
            Alert.pair_key == pair_key,
            Alert.triggered_at >= latest.computed_at - timedelta(hours=1),
            Alert.alert_type == "score_jump",
        ).first()

        if not existing:
            alerts.append(Alert(
                country_a=latest.country_a,
                country_b=latest.country_b,
                pair_key=pair_key,
                alert_type="score_jump",
                title=f"⚠️ Risk jumped +{delta:.0f} pts for {latest.country_a}-{latest.country_b}",
                message=(
                    f"Geopolitical risk between {latest.country_a} and {latest.country_b} "
                    f"rose sharply from {prev.score:.0f} to {latest.score:.0f} "
                    f"in the last {time_diff_hours:.1f} hours. "
                    f"Current level: {latest.classification}."
                ),
                prev_score=prev.score,
                new_score=latest.score,
                score_delta=delta,
                new_classification=latest.classification,
                severity=SEVERITY_MAP.get(latest.classification, "WARNING"),
            ))

    # ── Alert Condition 2: Crossed into new risk tier ─────────────────────────
    if latest.classification != prev.classification:
        tier_order = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}
        if tier_order.get(latest.classification, 0) > tier_order.get(prev.classification, 0):
            existing = db.query(Alert).filter(
                Alert.pair_key == pair_key,
                Alert.triggered_at >= latest.computed_at - timedelta(hours=2),
                Alert.alert_type == "tier_change",
            ).first()

            if not existing:
                alerts.append(Alert(
                    country_a=latest.country_a,
                    country_b=latest.country_b,
                    pair_key=pair_key,
                    alert_type="tier_change",
                    title=f"🚨 {latest.country_a}-{latest.country_b} escalated to {latest.classification}",
                    message=(
                        f"Risk level between {latest.country_a} and {latest.country_b} "
                        f"has escalated from {prev.classification} to {latest.classification}. "
                        f"Score: {latest.score:.0f}/100."
                    ),
                    prev_score=prev.score,
                    new_score=latest.score,
                    score_delta=delta,
                    new_classification=latest.classification,
                    severity=SEVERITY_MAP.get(latest.classification, "WARNING"),
                ))

    # ── Alert Condition 3: CRITICAL threshold crossed ─────────────────────────
    if latest.score >= 80 and prev.score < 80:
        existing = db.query(Alert).filter(
            Alert.pair_key == pair_key,
            Alert.triggered_at >= latest.computed_at - timedelta(hours=6),
            Alert.alert_type == "critical_threshold",
        ).first()
        if not existing:
            alerts.append(Alert(
                country_a=latest.country_a,
                country_b=latest.country_b,
                pair_key=pair_key,
                alert_type="critical_threshold",
                title=f"🔴 CRITICAL: {latest.country_a}-{latest.country_b} risk at {latest.score:.0f}/100",
                message=(
                    f"CRITICAL geopolitical risk threshold reached for "
                    f"{latest.country_a}-{latest.country_b}. "
                    f"Score: {latest.score:.0f}/100. Immediate monitoring recommended."
                ),
                prev_score=prev.score,
                new_score=latest.score,
                score_delta=delta,
                new_classification="CRITICAL",
                severity="CRITICAL",
            ))

    return alerts


class AlertChecker:
    def run(self) -> int:
        """
        Main entry point — called by scheduler every 15 mins.
        Returns number of alerts created.
        """
        logger.info("Alert checker starting...")
        total = 0

        with get_db_session() as db:
            # Get all unique pairs that have scores
            pairs = db.query(RiskScore.pair_key).distinct().all()
            pair_keys = [p[0] for p in pairs]

        for pair_key in pair_keys:
            try:
                with get_db_session() as db:
                    new_alerts = _check_pair(pair_key, db)
                    for alert in new_alerts:
                        db.add(alert)
                        logger.warning(f"Alert created: {alert.title}")
                    total += len(new_alerts)
            except Exception as e:
                logger.error(f"Alert check failed for {pair_key}: {e}")

        logger.info(f"Alert checker done: {total} new alerts.")
        return total

