"""
seed_demo.py
────────────
Seeds the database with realistic demo data so the UI is fully populated
immediately after startup — no waiting for scrapers or ML pipeline.

Safe to run multiple times (idempotent).

Usage:
    python seed_demo.py
    # or called automatically from main.py if settings.seed_demo_data=True
"""
import logging
import random
from datetime import datetime, timedelta

from database import get_db_session, init_db
from models.risk_score import RiskScore
from models.market_snapshot import MarketSnapshot
from models.alert import Alert
from models.intel_brief import IntelBrief
from models.sentiment_score import SentimentScore
from models.gdelt_event import GdeltEvent

logger = logging.getLogger(__name__)

# ── Tracked pairs with realistic baseline scores ──────────────────────────────
DEMO_PAIRS = [
    ("CN", "US", 74.2, "HIGH",     6.1),
    ("IN", "PK", 88.5, "CRITICAL", 3.4),
    ("RU", "UA", 91.0, "CRITICAL", -2.1),
    ("IL", "IR", 82.3, "CRITICAL", 8.7),
    ("IN", "CN", 61.4, "HIGH",     4.2),
    ("KP", "US", 67.8, "HIGH",     1.5),
    ("KP", "KR", 58.9, "MODERATE", -3.2),
    ("IL", "SA", 38.1, "MODERATE", 2.0),
    ("RU", "GB", 55.6, "MODERATE", 5.8),
    ("IN", "US", 22.4, "LOW",      -1.0),
    ("CN", "TW", 79.1, "HIGH",     7.3),
    ("TR", "GR", 44.7, "MODERATE", 0.5),
]

DEMO_MARKET = {
    "vix": 22.4,
    "sp500": 5234.18,
    "sp500_change_pct": -0.43,
    "crude_oil": 78.92,
    "gold": 2341.50,
    "dxy": 104.32,
    "market_stress_score": 0.42,
}

DEMO_ALERTS = [
    ("IN", "PK", "CRITICAL", "score_jump",
     "Risk surged +8.7 pts for IN-PK",
     "Geopolitical risk between India and Pakistan rose sharply following cross-border incidents. Current level: CRITICAL."),
    ("IL", "IR", "CRITICAL", "critical_threshold",
     "CRITICAL threshold reached: IL-IR at 82/100",
     "Risk between Israel and Iran has crossed the critical threshold. Immediate monitoring recommended."),
    ("RU", "UA", "CRITICAL", "tier_change",
     "RU-UA escalated to CRITICAL",
     "Risk level between Russia and Ukraine has escalated. Score: 91/100."),
    ("CN", "US", "WARNING", "score_jump",
     "Risk jumped +6.1 pts for CN-US",
     "US-China tensions elevated following trade and technology disputes."),
    ("CN", "TW", "WARNING", "score_jump",
     "CN-TW risk elevated to HIGH",
     "Cross-strait tensions have increased. Score: 79/100."),
    ("IN", "CN", "WARNING", "tier_change",
     "IN-CN escalated to HIGH",
     "India-China border tensions contributing to elevated risk score."),
]

BRIEF_TEMPLATES = {
    "CRITICAL": {
        "headline": "{a}–{b} Relations at Critical Juncture Amid Escalating Tensions",
        "summary": (
            "Geopolitical risk between {a} and {b} has reached a critical threshold, "
            "driven by sustained hostile rhetoric, elevated conflict event frequency, "
            "and deteriorating bilateral sentiment across monitored channels. "
            "Multiple indicators point to a high-probability escalation scenario "
            "requiring immediate attention from risk managers and policymakers."
        ),
        "key_drivers": [
            "Sustained hostile rhetoric from senior political figures on both sides",
            "GDELT conflict event frequency significantly above 72-hour baseline",
            "Rapid deterioration in public sentiment across social media channels",
            "Market stress indicators amplifying geopolitical risk premium",
        ],
        "market_implications": (
            "Elevated tensions may trigger safe-haven flows into gold and USD, "
            "with potential spillover to regional equity markets and energy prices."
        ),
        "outlook_72hr": (
            "Risk of further escalation remains elevated. "
            "Diplomatic de-escalation signals would be required to reverse current trajectory."
        ),
        "confidence": 0.82,
    },
    "HIGH": {
        "headline": "{a}–{b} Bilateral Tensions Remain Elevated",
        "summary": (
            "Relations between {a} and {b} are under significant strain. "
            "Sentiment analysis and GDELT conflict data indicate a sustained deterioration "
            "in bilateral dynamics over the past 72 hours. "
            "Escalation risk remains elevated, though no acute crisis is imminent."
        ),
        "key_drivers": [
            "Negative sentiment trend accelerating across monitored channels",
            "Multiple GDELT conflict events detected in bilateral context",
            "Politician hostility scores above threshold",
        ],
        "market_implications": (
            "Continued tensions may weigh on regional market sentiment "
            "and affect bilateral trade flows."
        ),
        "outlook_72hr": (
            "Situation likely to remain tense. "
            "Watch for diplomatic statements or military posturing as leading indicators."
        ),
        "confidence": 0.74,
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
        "confidence": 0.65,
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
}


def _already_seeded(db) -> bool:
    """Check if demo data already exists."""
    return db.query(RiskScore).count() > 0


def seed_market_snapshots(db) -> None:
    """Seed 48 hours of market snapshots (hourly)."""
    if db.query(MarketSnapshot).count() > 0:
        return
    now = datetime.utcnow()
    for h in range(48, 0, -1):
        ts = now - timedelta(hours=h)
        # Add slight random variation
        jitter = lambda v, pct=0.02: round(v * (1 + random.uniform(-pct, pct)), 2)
        db.add(MarketSnapshot(
            captured_at=ts,
            vix=jitter(DEMO_MARKET["vix"], 0.05),
            sp500=jitter(DEMO_MARKET["sp500"], 0.01),
            sp500_change_pct=round(random.uniform(-0.8, 0.4), 3),
            crude_oil=jitter(DEMO_MARKET["crude_oil"], 0.02),
            gold=jitter(DEMO_MARKET["gold"], 0.01),
            dxy=jitter(DEMO_MARKET["dxy"], 0.005),
            market_stress_score=round(random.uniform(0.30, 0.55), 3),
        ))
    logger.info("Market snapshots seeded (48h)")


def seed_sentiment_scores(db) -> None:
    """Seed 72h of hourly sentiment scores for each tracked country."""
    if db.query(SentimentScore).count() > 0:
        return
    countries = list({c for pair in DEMO_PAIRS for c in (pair[0], pair[1])})
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

    # Base sentiment per country (negative = hostile)
    base_sentiment = {
        "CN": -0.35, "US": -0.28, "RU": -0.62, "UA": -0.58,
        "IN": -0.31, "PK": -0.44, "IL": -0.52, "IR": -0.61,
        "KP": -0.70, "KR": -0.25, "SA": -0.18, "GB": -0.15,
        "TW": -0.40, "TR": -0.22, "GR": -0.18,
    }

    for country in countries:
        base = base_sentiment.get(country, -0.20)
        for h in range(72, 0, -1):
            bucket = now - timedelta(hours=h)
            drift = random.uniform(-0.05, 0.05)
            avg = round(max(-1.0, min(1.0, base + drift)), 4)
            db.add(SentimentScore(
                country_code=country,
                time_bucket=bucket,
                avg_sentiment=avg,
                weighted_sentiment=round(avg * 0.95, 4),
                sentiment_delta=round(random.uniform(-0.08, 0.08), 4),
                politician_sentiment=round(avg - 0.1, 4),
                public_sentiment=round(avg + 0.05, 4),
                post_count=random.randint(15, 120),
                negative_ratio=round(max(0, min(1, 0.5 - avg * 0.4)), 4),
                high_hostility_count=random.randint(0, 8),
                post_volume_spike=round(random.uniform(-0.5, 1.5), 3),
                computed_at=bucket,
            ))
    logger.info(f"Sentiment scores seeded ({len(countries)} countries × 72h)")


def seed_risk_scores(db) -> None:
    """Seed risk scores — 3 historical + 1 current per pair."""
    if db.query(RiskScore).count() > 0:
        return
    now = datetime.utcnow()
    for a, b, score, classification, delta in DEMO_PAIRS:
        pair_key = RiskScore.make_pair_key(a, b)
        prev_score = round(score - delta, 2)

        # 3 historical scores (24h, 48h, 72h ago)
        for h in [72, 48, 24]:
            hist_score = round(score - delta * (h / 24), 2)
            db.add(RiskScore(
                country_a=a, country_b=b, pair_key=pair_key,
                score=hist_score,
                classification=RiskScore.classify(hist_score),
                negative_sentiment_score=round(random.uniform(0.3, 0.7), 3),
                sentiment_deterioration_rate=round(random.uniform(0.1, 0.5), 3),
                politician_hostility_score=round(random.uniform(0.2, 0.6), 3),
                gdelt_conflict_intensity=round(random.uniform(0.2, 0.7), 3),
                vix_spike_score=round(random.uniform(0.1, 0.4), 3),
                market_stress_score=round(random.uniform(0.2, 0.5), 3),
                post_count_a=random.randint(20, 150),
                post_count_b=random.randint(20, 150),
                gdelt_event_count=random.randint(2, 18),
                contributing_factors=[],
                prev_score=None,
                score_change=0.0,
                computed_at=now - timedelta(hours=h),
            ))

        # Current score
        factors = _build_factors(a, b, score, classification)
        db.add(RiskScore(
            country_a=a, country_b=b, pair_key=pair_key,
            score=score,
            classification=classification,
            negative_sentiment_score=round(random.uniform(0.4, 0.8), 3),
            sentiment_deterioration_rate=round(random.uniform(0.2, 0.6), 3),
            politician_hostility_score=round(random.uniform(0.3, 0.7), 3),
            gdelt_conflict_intensity=round(random.uniform(0.3, 0.8), 3),
            vix_spike_score=round(random.uniform(0.2, 0.5), 3),
            market_stress_score=round(random.uniform(0.3, 0.6), 3),
            post_count_a=random.randint(50, 300),
            post_count_b=random.randint(50, 300),
            gdelt_event_count=random.randint(5, 25),
            contributing_factors=factors,
            prev_score=prev_score,
            score_change=delta,
            computed_at=now,
        ))
    logger.info(f"Risk scores seeded ({len(DEMO_PAIRS)} pairs)")


def _build_factors(a: str, b: str, score: float, level: str):
    factors = []
    if score > 60:
        factors.append({
            "factor": f"High negative sentiment in {a}-{b} discourse",
            "impact": 0.22, "category": "sentiment",
        })
    if score > 70:
        factors.append({
            "factor": "Rapidly deteriorating rhetoric in last 72 hours",
            "impact": 0.18, "category": "trend",
        })
    if score > 75:
        factors.append({
            "factor": "Hostile language from tracked political leaders",
            "impact": 0.15, "category": "political",
        })
    if score > 65:
        factors.append({
            "factor": f"GDELT detected multiple conflict events in 72h window",
            "impact": 0.14, "category": "events",
        })
    return sorted(factors, key=lambda x: x["impact"], reverse=True)


def seed_alerts(db) -> None:
    """Seed realistic alerts."""
    if db.query(Alert).count() > 0:
        return
    now = datetime.utcnow()
    for i, (a, b, severity, atype, title, message) in enumerate(DEMO_ALERTS):
        pair_key = RiskScore.make_pair_key(a, b)
        db.add(Alert(
            country_a=a, country_b=b, pair_key=pair_key,
            alert_type=atype, title=title, message=message,
            severity=severity,
            prev_score=50.0, new_score=75.0, score_delta=25.0,
            new_classification=severity if severity == "CRITICAL" else "HIGH",
            is_read=(i > 2),  # First 3 unread
            triggered_at=now - timedelta(hours=i * 3 + 1),
        ))
    logger.info(f"Alerts seeded ({len(DEMO_ALERTS)} alerts)")


def seed_briefs(db) -> None:
    """Seed intelligence briefs for all tracked pairs."""
    if db.query(IntelBrief).count() > 0:
        return
    now = datetime.utcnow()
    for a, b, score, classification, _ in DEMO_PAIRS:
        pair_key = RiskScore.make_pair_key(a, b)
        tmpl = BRIEF_TEMPLATES.get(classification, BRIEF_TEMPLATES["MODERATE"])
        a_name = COUNTRY_NAMES.get(a, a)
        b_name = COUNTRY_NAMES.get(b, b)
        db.add(IntelBrief(
            country_a=a, country_b=b, pair_key=pair_key,
            risk_score_val=score,
            risk_level=classification,
            headline=tmpl["headline"].format(a=a_name, b=b_name),
            summary=tmpl["summary"].format(a=a_name, b=b_name),
            key_drivers=tmpl["key_drivers"],
            market_implications=tmpl["market_implications"],
            outlook_72hr=tmpl["outlook_72hr"],
            confidence=tmpl["confidence"],
            trigger="seed",
            generated_at=now - timedelta(hours=2),
            expires_at=now + timedelta(hours=4),
        ))
    logger.info(f"Intelligence briefs seeded ({len(DEMO_PAIRS)} pairs)")


def seed_gdelt_events(db) -> None:
    """Seed sample GDELT conflict events."""
    if db.query(GdeltEvent).count() > 0:
        return
    now = datetime.utcnow()
    events = [
        ("IN", "PK", "190", -8.5, 42, "Lahore, Pakistan"),
        ("RU", "UA", "195", -9.0, 87, "Kyiv, Ukraine"),
        ("IL", "IR", "190", -8.0, 63, "Tehran, Iran"),
        ("CN", "US", "172", -6.5, 55, "South China Sea"),
        ("CN", "TW", "195", -8.8, 71, "Taiwan Strait"),
        ("KP", "US", "172", -7.2, 38, "Korean Peninsula"),
        ("IN", "CN", "172", -6.0, 29, "Line of Actual Control"),
        ("RU", "GB", "172", -5.5, 22, "Eastern Europe"),
    ]
    for i, (a, b, code, gs, articles, geo) in enumerate(events):
        db.add(GdeltEvent(
            gdelt_event_id=f"SEED_{i:04d}",
            event_date=now - timedelta(hours=random.randint(1, 48)),
            actor1_country=a, actor2_country=b,
            event_code=code,
            goldstein_scale=gs,
            num_articles=articles,
            num_sources=max(1, articles // 5),
            avg_tone=round(gs * 1.2, 2),
            action_geo_name=geo,
            fetched_at=now,
        ))
    logger.info(f"GDELT events seeded ({len(events)} events)")


def run_seed():
    """Main entry point — seeds all demo data."""
    logger.info("Seeding demo data...")
    with get_db_session() as db:
        if _already_seeded(db):
            logger.info("Demo data already present — skipping seed.")
            return
        seed_market_snapshots(db)
        seed_sentiment_scores(db)
        seed_risk_scores(db)
        seed_alerts(db)
        seed_briefs(db)
        seed_gdelt_events(db)
    logger.info("Demo data seeding complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    init_db()
    run_seed()
    print("Done.")
