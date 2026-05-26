"""
reseed_briefs.py — Re-seeds intel briefs to match current risk scores.
Usage: python reseed_briefs.py
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import func

from database import get_db_session, init_db
from models.intel_brief import IntelBrief
from models.risk_score import RiskScore

logging.basicConfig(level=logging.WARNING)

BRIEF_TEMPLATES = {
    "CRITICAL": {
        "headline": "{a}–{b} Relations at Critical Juncture — Escalation Risk Extreme",
        "summary": (
            "Geopolitical risk between {a} and {b} has reached a critical threshold. "
            "Multiple indicators — including hostile political rhetoric, elevated conflict events, "
            "and deteriorating bilateral sentiment — point to a high-probability escalation scenario. "
            "Immediate monitoring and contingency planning are advised."
        ),
        "key_drivers": [
            "Extreme hostile sentiment and near-war indicators in bilateral discourse",
            "Elevated GDELT conflict event frequency (GoldsteinScale < -8)",
            "Rapid deterioration in public and political sentiment over 72-hour window",
            "Market stress indicators amplifying geopolitical risk premium",
        ],
        "market_implications": (
            "Elevated tensions may trigger safe-haven flows into gold and USD, "
            "with potential spillover to regional equity markets and energy prices."
        ),
        "outlook_72hr": (
            "Risk of further escalation remains extreme. "
            "Diplomatic de-escalation signals would be required to reverse current trajectory."
        ),
        "confidence": 0.88,
    },
    "HIGH": {
        "headline": "{a}–{b} Bilateral Tensions Elevated — Escalation Risk Significant",
        "summary": (
            "Relations between {a} and {b} are under significant strain. "
            "Sentiment analysis and GDELT conflict data indicate a sustained deterioration "
            "in bilateral dynamics over the past 72 hours. "
            "Escalation risk remains elevated, with multiple flashpoints requiring close monitoring."
        ),
        "key_drivers": [
            "Elevated negative sentiment trend accelerating across monitored channels",
            "Multiple GDELT conflict events detected in bilateral context",
            "Politician hostility scores above threshold on both sides",
            "Strategic competition intensifying across multiple domains",
        ],
        "market_implications": (
            "Continued tensions may weigh on regional market sentiment, "
            "affect bilateral trade flows, and drive safe-haven demand."
        ),
        "outlook_72hr": (
            "Situation likely to remain tense. "
            "Watch for diplomatic statements or military posturing as leading indicators."
        ),
        "confidence": 0.80,
    },
    "MODERATE": {
        "headline": "{a}–{b} Relationship Shows Moderate Stress Signals",
        "summary": (
            "The {a}–{b} relationship shows moderate stress signals. "
            "While no acute crisis is imminent, negative sentiment trends and "
            "periodic conflict events warrant continued monitoring."
        ),
        "key_drivers": [
            "Moderate negative sentiment with periodic spikes",
            "Isolated conflict events without sustained escalation pattern",
            "Market indicators showing mild stress correlation",
        ],
        "market_implications": (
            "Current risk level has limited direct market implications "
            "but warrants monitoring for escalation signals."
        ),
        "outlook_72hr": "Situation expected to remain stable barring new developments.",
        "confidence": 0.70,
    },
    "LOW": {
        "headline": "{a}–{b} Bilateral Environment Remains Stable",
        "summary": (
            "Current indicators for {a}–{b} suggest a relatively stable bilateral environment. "
            "Sentiment remains broadly neutral and conflict event frequency is within normal range."
        ),
        "key_drivers": [
            "Sentiment broadly neutral or positive",
            "No significant GDELT conflict events in 72-hour window",
            "Market indicators stable",
        ],
        "market_implications": "No significant market implications at current risk level.",
        "outlook_72hr": "Stable outlook. Routine monitoring sufficient.",
        "confidence": 0.78,
    },
}

COUNTRY_NAMES = {
    "US": "United States", "CN": "China", "RU": "Russia", "IN": "India",
    "PK": "Pakistan", "UA": "Ukraine", "IL": "Israel", "IR": "Iran",
    "KP": "North Korea", "KR": "South Korea", "SA": "Saudi Arabia",
    "GB": "United Kingdom", "TW": "Taiwan", "TR": "Turkey", "GR": "Greece",
    "JP": "Japan", "DE": "Germany", "FR": "France", "CA": "Canada",
    "PS": "Palestine",
}


def reseed_briefs():
    init_db()
    now = datetime.utcnow()
    count = 0

    with get_db_session() as db:
        # Get latest risk score per pair
        latest_subq = (
            db.query(RiskScore.pair_key, func.max(RiskScore.computed_at).label("latest"))
            .group_by(RiskScore.pair_key)
            .subquery()
        )
        latest_scores = (
            db.query(RiskScore)
            .join(
                latest_subq,
                (RiskScore.pair_key == latest_subq.c.pair_key)
                & (RiskScore.computed_at == latest_subq.c.latest),
            )
            .all()
        )

        for risk in latest_scores:
            tmpl = BRIEF_TEMPLATES.get(risk.classification, BRIEF_TEMPLATES["LOW"])
            a_name = COUNTRY_NAMES.get(risk.country_a, risk.country_a)
            b_name = COUNTRY_NAMES.get(risk.country_b, risk.country_b)
            db.add(
                IntelBrief(
                    country_a=risk.country_a,
                    country_b=risk.country_b,
                    pair_key=risk.pair_key,
                    risk_score_val=risk.score,
                    risk_level=risk.classification,
                    headline=tmpl["headline"].format(a=a_name, b=b_name),
                    summary=tmpl["summary"].format(a=a_name, b=b_name),
                    key_drivers=tmpl["key_drivers"],
                    market_implications=tmpl["market_implications"],
                    outlook_72hr=tmpl["outlook_72hr"],
                    confidence=tmpl["confidence"],
                    trigger="reseed",
                    generated_at=now - timedelta(minutes=5),
                    expires_at=now + timedelta(hours=6),
                )
            )
            count += 1
            print(f"  OK {risk.pair_key}: {risk.score:.0f} ({risk.classification})")

        db.commit()
        print(f"\nSeeded {count} intel briefs matching new risk scores.")


if __name__ == "__main__":
    reseed_briefs()
