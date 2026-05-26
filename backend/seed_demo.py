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
from config import settings

logger = logging.getLogger(__name__)

# ── Tracked pairs with realistic baseline scores (as of May 22, 2026) ─────────
# Based on actual geopolitical conditions from currentgeo.txt
# Format: (country_a, country_b, score, classification, recent_delta)
DEMO_PAIRS = [
    # CRITICAL — Active conflicts and near-war scenarios
    ("IL", "IR", 96.0, "CRITICAL", 4.1),   # Israel-Iran: near-war, direct strikes exchanged
    ("US", "IR", 96.0, "CRITICAL", 3.8),   # US-Iran: nuclear brinkmanship, maximum pressure
    ("RU", "UA", 95.0, "CRITICAL", 2.1),   # Active war - most dangerous active interstate war
    ("IL", "PS", 88.0, "CRITICAL", 2.9),   # Israel-Palestine: ongoing conflict, humanitarian crisis

    # HIGH — Serious tensions with escalation risk
    ("US", "CN", 74.0, "HIGH", 2.2),       # Trade war escalation, Taiwan flashpoint
    ("KP", "KR", 63.0, "HIGH", 1.4),       # Korean Peninsula: provocations, military posturing
    ("IN", "PK", 62.0, "HIGH", -0.8),      # Post-conflict ceasefire under strain
    ("RU", "US", 69.0, "HIGH", 1.6),       # Proxy war, nuclear signalling, sanctions
    ("GB", "US", 46.0, "MODERATE", 0.6),   # Trade friction, post-Brexit tensions

    # MODERATE — Managed tensions
    ("CN", "TW", 51.0, "MODERATE", 1.2),   # Cross-strait military pressure
    ("CN", "IN", 52.0, "MODERATE", 0.9),   # Border standoffs, LAC friction
    ("CN", "JP", 38.0, "MODERATE", 0.5),   # East China Sea, Senkaku disputes

    # LOW — Stable or managed relations
    ("KP", "US", 22.0, "LOW", 0.3),        # Diplomatic engagement continuing
    ("RU", "GB", 14.0, "LOW", 0.4),        # Sanctions in place but stable
    ("RU", "DE", 13.0, "LOW", 0.1),        # Energy decoupling complete, stable
    ("RU", "FR", 12.0, "LOW", -0.1),       # European security stable
    ("CN", "DE", 11.0, "LOW", 0.2),        # Industrial competition managed
    ("CN", "FR", 10.0, "LOW", 0.1),        # Strategic hedging stable
    ("CN", "GB", 10.0, "LOW", 0.2),        # Indo-Pacific friction minimal
    ("IN", "US", 9.0, "LOW", -0.2),        # Strong strategic partnership
    ("CA", "CN", 9.0, "LOW", 0.1),         # Diplomatic channels open
    ("TR", "GR", 8.0, "LOW", 0.1),         # Eastern Mediterranean stable
    ("RU", "CA", 8.0, "LOW", 0.2),         # Arctic cooperation limited but stable
    ("IR", "GB", 8.0, "LOW", 0.1),         # Maritime tensions minimal
    ("IR", "FR", 7.0, "LOW", 0.1),         # Nuclear diplomacy ongoing
    ("IR", "DE", 7.0, "LOW", 0.1),         # EU sanctions stable
    ("IL", "SA", 6.0, "LOW", -0.3),        # Quiet normalization progressing
    ("RU", "JP", 6.0, "LOW", 0.1),         # Kuril dispute frozen but stable
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
    ("IL", "IR", "CRITICAL", "critical_threshold",
     "CRITICAL: IL-IR near-war environment at 96/100",
     "Israel-Iran tensions have reached maximum risk. Direct strikes exchanged; one miscalculation could trigger full regional war. Risk level: CRITICAL (96/100)."),
    ("US", "IR", "CRITICAL", "critical_threshold",
     "CRITICAL: US-IR nuclear brinkmanship at 96/100",
     "United States-Iran nuclear standoff at peak intensity. Maximum pressure campaign, regional military deployments, and sanctions escalation. Risk level: CRITICAL (96/100)."),
    ("RU", "UA", "CRITICAL", "critical_threshold",
     "CRITICAL: RU-UA active war at 95/100",
     "Russia-Ukraine conflict remains the most dangerous active interstate war globally. Risk level: CRITICAL (95/100)."),
    ("IL", "PS", "CRITICAL", "score_jump",
     "CRITICAL: IL-PS ongoing conflict at 88/100",
     "Israeli-Palestinian conflict continues with sustained military operations. Humanitarian crisis deepening. Risk level: CRITICAL (88/100)."),
    ("US", "CN", "HIGH", "score_jump",
     "HIGH: US-CN trade war escalation at 74/100",
     "US-China tensions elevated across trade, technology, and Taiwan flashpoint. Risk level: HIGH (74/100)."),
    ("RU", "US", "HIGH", "tier_change",
     "HIGH: RU-US proxy conflict and nuclear signalling at 69/100",
     "Russia-US tensions driven by Ukraine proxy war, nuclear rhetoric, and sanctions. Risk level: HIGH (69/100)."),
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
    "JP": "Japan", "DE": "Germany", "FR": "France", "CA": "Canada",
    "PS": "Palestine",
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
    """
    Seed 72h of hourly sentiment scores for each tracked country.
    Values are calibrated so the LR model produces realistic, varied
    risk scores — not all-100 or all-0.
    """
    if db.query(SentimentScore).count() > 0:
        return
    countries = list({c for pair in DEMO_PAIRS for c in (pair[0], pair[1])})
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

    # Sentiment calibrated to produce realistic LR outputs.
    # LR saturates at 100 when avg_sentiment < -0.5 (neg_ratio ≈ 0.75+).
    # Keep values in a range that produces varied model outputs.
    # Scale: -1.0 = very hostile, 0.0 = neutral, +1.0 = cooperative
    base_sentiment = {
        # CRITICAL (96) — IL-IR, US-IR: near-war / nuclear brinkmanship
        "IL": -0.52, "IR": -0.50,
        # CRITICAL (95) — RU-UA: active war
        "RU": -0.48, "UA": -0.46,
        # CRITICAL (88) — IL-PS: ongoing conflict
        "PS": -0.44,
        # HIGH (74) — US-CN: trade war + Taiwan
        "US": -0.38,
        # HIGH (69) — RU-US already covered; CN also HIGH context
        "CN": -0.34,
        # HIGH (63) — KP-KR
        "KP": -0.32, "KR": -0.28,
        # HIGH (62) — IN-PK
        "IN": -0.26, "PK": -0.24,
        # MODERATE (51-52) — CN-TW, CN-IN
        "TW": -0.18,
        # MODERATE (46) — GB-US
        "GB": -0.14,
        # MODERATE (38) — CN-JP
        "JP": -0.12,
        # LOW — stable relations
        "DE": -0.06, "FR": -0.05,
        "SA": -0.02, "TR": -0.03,
        "GR": -0.02, "CA": -0.02,
    }

    for country in countries:
        base = base_sentiment.get(country, -0.10)
        for h in range(72, 0, -1):
            bucket = now - timedelta(hours=h)
            drift = random.uniform(-0.04, 0.04)
            avg = round(max(-0.6, min(0.4, base + drift)), 4)
            neg_ratio = round(max(0.0, min(1.0, 0.5 - avg * 0.4)), 4)
            db.add(SentimentScore(
                country_code=country,
                time_bucket=bucket,
                avg_sentiment=avg,
                weighted_sentiment=round(avg * 0.95, 4),
                sentiment_delta=round(random.uniform(-0.04, 0.04), 4),
                politician_sentiment=round(avg - 0.05, 4),
                public_sentiment=round(avg + 0.03, 4),
                post_count=random.randint(15, 120),
                negative_ratio=neg_ratio,
                high_hostility_count=random.randint(0, 4),
                post_volume_spike=round(random.uniform(-0.3, 0.8), 3),
                computed_at=bucket,
            ))
    logger.info(f"Sentiment scores seeded ({len(countries)} countries × 72h)")


def seed_risk_scores(db) -> None:
    """
    Seed risk scores with realistic, varied values.

    Always seeds — regardless of MODEL_BACKEND — so the dashboard shows
    meaningful data immediately. The scheduler will overwrite these with
    real model-computed scores on its first run once live data flows in.

    Score distribution:
      CRITICAL (≥80): RU-UA, IL-IR
      HIGH     (≥60): US-IR, IL-PS
      LOW      (<30): All others
    """
    if db.query(RiskScore).count() > 0:
        return

    now = datetime.utcnow()
    for a, b, score, classification, delta in DEMO_PAIRS:
        pair_key = RiskScore.make_pair_key(a, b)
        prev_score = round(score - delta, 2)

        # 3 historical scores (24h, 48h, 72h ago)
        for h in [72, 48, 24]:
            hist_score = round(score - delta * (h / 24), 2)
            
            # Component scores based on risk level
            if score >= 80:  # CRITICAL
                neg_sent = round(random.uniform(0.75, 0.92), 3)
                sent_det = round(random.uniform(0.65, 0.82), 3)
                pol_host = round(random.uniform(0.70, 0.88), 3)
                gdelt_int = round(random.uniform(0.72, 0.90), 3)
            elif score >= 60:  # HIGH
                neg_sent = round(random.uniform(0.55, 0.72), 3)
                sent_det = round(random.uniform(0.45, 0.62), 3)
                pol_host = round(random.uniform(0.50, 0.68), 3)
                gdelt_int = round(random.uniform(0.52, 0.70), 3)
            elif score >= 35:  # MODERATE
                neg_sent = round(random.uniform(0.30, 0.48), 3)
                sent_det = round(random.uniform(0.22, 0.38), 3)
                pol_host = round(random.uniform(0.28, 0.44), 3)
                gdelt_int = round(random.uniform(0.28, 0.44), 3)
            else:  # LOW
                neg_sent = round(random.uniform(0.10, 0.25), 3)
                sent_det = round(random.uniform(0.05, 0.15), 3)
                pol_host = round(random.uniform(0.08, 0.20), 3)
                gdelt_int = round(random.uniform(0.10, 0.25), 3)
            
            db.add(RiskScore(
                country_a=a, country_b=b, pair_key=pair_key,
                score=hist_score,
                classification=RiskScore.classify(hist_score),
                negative_sentiment_score=neg_sent,
                sentiment_deterioration_rate=sent_det,
                politician_hostility_score=pol_host,
                gdelt_conflict_intensity=gdelt_int,
                vix_spike_score=round(random.uniform(0.1, 0.3), 3),
                market_stress_score=round(random.uniform(0.2, 0.4), 3),
                post_count_a=random.randint(20, 100),
                post_count_b=random.randint(20, 100),
                gdelt_event_count=random.randint(2, 12),
                contributing_factors=[],
                prev_score=None,
                score_change=0.0,
                computed_at=now - timedelta(hours=h),
            ))

        # Current score with proper component scores
        if score >= 80:  # CRITICAL
            neg_sent = round(random.uniform(0.78, 0.94), 3)
            sent_det = round(random.uniform(0.68, 0.85), 3)
            pol_host = round(random.uniform(0.72, 0.90), 3)
            gdelt_int = round(random.uniform(0.75, 0.92), 3)
            post_a = random.randint(150, 400)
            post_b = random.randint(150, 400)
            events = random.randint(20, 40)
        elif score >= 60:  # HIGH
            neg_sent = round(random.uniform(0.58, 0.75), 3)
            sent_det = round(random.uniform(0.48, 0.65), 3)
            pol_host = round(random.uniform(0.52, 0.70), 3)
            gdelt_int = round(random.uniform(0.55, 0.72), 3)
            post_a = random.randint(80, 220)
            post_b = random.randint(80, 220)
            events = random.randint(10, 22)
        elif score >= 35:  # MODERATE
            neg_sent = round(random.uniform(0.32, 0.50), 3)
            sent_det = round(random.uniform(0.24, 0.40), 3)
            pol_host = round(random.uniform(0.30, 0.46), 3)
            gdelt_int = round(random.uniform(0.30, 0.46), 3)
            post_a = random.randint(40, 120)
            post_b = random.randint(40, 120)
            events = random.randint(4, 12)
        else:  # LOW
            neg_sent = round(random.uniform(0.12, 0.28), 3)
            sent_det = round(random.uniform(0.08, 0.18), 3)
            pol_host = round(random.uniform(0.10, 0.25), 3)
            gdelt_int = round(random.uniform(0.12, 0.28), 3)
            post_a = random.randint(30, 80)
            post_b = random.randint(30, 80)
            events = random.randint(3, 8)
        
        factors = _build_factors(a, b, score, classification)
        db.add(RiskScore(
            country_a=a, country_b=b, pair_key=pair_key,
            score=score,
            classification=classification,
            negative_sentiment_score=neg_sent,
            sentiment_deterioration_rate=sent_det,
            politician_hostility_score=pol_host,
            gdelt_conflict_intensity=gdelt_int,
            vix_spike_score=round(random.uniform(0.2, 0.4), 3),
            market_stress_score=round(random.uniform(0.3, 0.5), 3),
            post_count_a=post_a,
            post_count_b=post_b,
            gdelt_event_count=events,
            contributing_factors=factors,
            prev_score=prev_score,
            score_change=delta,
            computed_at=now,
        ))
    logger.info(f"Risk scores seeded ({len(DEMO_PAIRS)} pairs)")


def _build_factors(a: str, b: str, score: float, level: str):
    factors = []
    if score >= 80:  # CRITICAL
        factors.append({
            "factor": f"Extreme hostile sentiment in {a}-{b} discourse — near-war indicators",
            "impact": 0.28, "category": "sentiment",
        })
        factors.append({
            "factor": "Rapidly deteriorating rhetoric and military posturing in last 72 hours",
            "impact": 0.24, "category": "trend",
        })
        factors.append({
            "factor": "Hostile language and threats from senior political and military leaders",
            "impact": 0.20, "category": "political",
        })
        factors.append({
            "factor": "GDELT detected multiple high-severity conflict events in 72h window",
            "impact": 0.18, "category": "events",
        })
    elif score >= 60:  # HIGH
        factors.append({
            "factor": f"Elevated negative sentiment in {a}-{b} discourse with escalation signals",
            "impact": 0.20, "category": "sentiment",
        })
        factors.append({
            "factor": "Deteriorating bilateral rhetoric and diplomatic friction",
            "impact": 0.16, "category": "trend",
        })
        factors.append({
            "factor": "Hostile statements from political figures on both sides",
            "impact": 0.13, "category": "political",
        })
        factors.append({
            "factor": "GDELT conflict events above baseline in monitoring window",
            "impact": 0.11, "category": "events",
        })
    elif score >= 35:  # MODERATE
        factors.append({
            "factor": f"Moderate negative sentiment in {a}-{b} bilateral discourse",
            "impact": 0.14, "category": "sentiment",
        })
        factors.append({
            "factor": "Periodic friction in bilateral dialogue and negotiations",
            "impact": 0.10, "category": "trend",
        })
        factors.append({
            "factor": "Isolated conflict events without sustained escalation pattern",
            "impact": 0.08, "category": "events",
        })
    else:  # LOW
        factors.append({
            "factor": f"Stable bilateral relations between {a} and {b}",
            "impact": 0.08, "category": "sentiment",
        })
        factors.append({
            "factor": "Minimal conflict events in monitoring period",
            "impact": 0.06, "category": "events",
        })
    return sorted(factors, key=lambda x: x["impact"], reverse=True)


def seed_alerts(db) -> None:
    """Seed realistic alerts with recent timestamps."""
    if db.query(Alert).count() > 0:
        return
    now = datetime.utcnow()
    for i, (a, b, severity, atype, title, message) in enumerate(DEMO_ALERTS):
        pair_key = RiskScore.make_pair_key(a, b)
        # Stagger timestamps: 1h, 3h, 6h, 10h, 18h, 26h ago
        hours_ago = [1, 3, 6, 10, 18, 26][i] if i < 6 else i * 4
        db.add(Alert(
            country_a=a, country_b=b, pair_key=pair_key,
            alert_type=atype, title=title, message=message,
            severity=severity,
            prev_score=50.0, new_score=75.0, score_delta=25.0,
            new_classification=severity if severity == "CRITICAL" else "HIGH",
            is_read=(i > 2),  # First 3 unread
            triggered_at=now - timedelta(hours=hours_ago),
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
    """Seed sample GDELT conflict events based on current geopolitical landscape."""
    if db.query(GdeltEvent).count() > 0:
        return
    now = datetime.utcnow()
    events = [
        # CRITICAL (96) — IL-IR, US-IR: near-war / nuclear brinkmanship
        ("IL", "IR", "195", -9.8, 112, "Tehran / Tel Aviv"),
        ("US", "IR", "195", -9.6, 98, "Persian Gulf / Strait of Hormuz"),
        # CRITICAL (95) — RU-UA: active war
        ("RU", "UA", "195", -9.2, 95, "Kyiv, Ukraine"),
        # CRITICAL (88) — IL-PS: ongoing conflict
        ("IL", "PS", "190", -8.8, 82, "Gaza Strip"),

        # HIGH (74) — US-CN
        ("US", "CN", "172", -6.8, 58, "South China Sea / Taiwan Strait"),
        # HIGH (69) — RU-US
        ("RU", "US", "172", -6.2, 48, "Eastern Europe / NATO Flank"),
        # HIGH (63) — KP-KR
        ("KP", "KR", "172", -5.8, 42, "Korean DMZ"),
        # HIGH (62) — IN-PK
        ("IN", "PK", "172", -5.5, 38, "Line of Control, Kashmir"),
        # MODERATE (52) — CN-IN
        ("CN", "IN", "042", -3.8, 22, "Himalayan Border / LAC"),
        # MODERATE (51) — CN-TW
        ("CN", "TW", "042", -3.5, 20, "Taiwan Strait"),
        # MODERATE (46) — GB-US
        ("GB", "US", "042", -2.8, 14, "London / Washington"),
        # MODERATE (38) — CN-JP
        ("CN", "JP", "042", -2.4, 12, "East China Sea / Senkaku Islands"),
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
