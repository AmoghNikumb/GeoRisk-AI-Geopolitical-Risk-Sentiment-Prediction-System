"""
services/groq_risk_scorer.py
────────────────────────────
Uses Groq LLM (llama-3.3-70b-versatile) to generate bilateral geopolitical
risk scores for each tracked country pair.

The LLM is prompted with:
  - The country pair
  - Any recent tweet sentiment signals from our DB (if available)
  - GDELT conflict event count (if available)
  - Current market stress (VIX, if available)

It returns a structured JSON with score (0-100), classification, contributing
factors, and reasoning — which is written directly to the RiskScore table.

The sentence-level classification pipeline (RoBERTa + pkl on ProcessedPost)
is NOT touched by this module.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from database import get_db_session
from models.risk_score import RiskScore
from models.sentiment_score import SentimentScore
from models.gdelt_event import GdeltEvent
from models.market_snapshot import MarketSnapshot
from scoring.risk_calculator import TRACKED_PAIRS

logger = logging.getLogger(__name__)

# Country code → human-readable name for the prompt
COUNTRY_NAMES = {
    "CN": "China",
    "US": "United States",
    "IN": "India",
    "PK": "Pakistan",
    "RU": "Russia",
    "UA": "Ukraine",
    "IL": "Israel",
    "IR": "Iran",
    "KP": "North Korea",
    "KR": "South Korea",
    "SA": "Saudi Arabia",
    "GB": "United Kingdom",
    "TW": "Taiwan",
    "TR": "Turkey",
    "GR": "Greece",
}


def _get_context(country_a: str, country_b: str, db) -> dict:
    """Pull available signals from DB to enrich the LLM prompt."""
    since = datetime.utcnow() - timedelta(hours=72)

    # Sentiment signals
    def get_sentiment(code):
        rows = db.query(SentimentScore).filter(
            SentimentScore.country_code == code,
            SentimentScore.time_bucket >= since,
        ).order_by(SentimentScore.time_bucket.desc()).limit(5).all()
        if not rows:
            return None
        avg = sum(r.avg_sentiment or 0 for r in rows) / len(rows)
        neg_ratio = rows[0].negative_ratio or 0
        return {"avg_sentiment": round(avg, 3), "negative_ratio": round(neg_ratio, 2), "post_count": sum(r.post_count for r in rows)}

    sent_a = get_sentiment(country_a)
    sent_b = get_sentiment(country_b)

    # GDELT conflict events
    gdelt_rows = db.query(GdeltEvent).filter(
        GdeltEvent.event_date >= since,
        GdeltEvent.goldstein_scale < -5,
    ).filter(
        (GdeltEvent.actor1_country.in_([country_a, country_b])) |
        (GdeltEvent.actor2_country.in_([country_a, country_b]))
    ).all()
    gdelt_count = len(gdelt_rows)
    gdelt_min_goldstein = min((e.goldstein_scale for e in gdelt_rows), default=0)

    # Market
    market = db.query(MarketSnapshot).order_by(MarketSnapshot.captured_at.desc()).first()
    vix = market.vix if market else None
    market_stress = market.market_stress_score if market else None

    return {
        "sentiment_a": sent_a,
        "sentiment_b": sent_b,
        "gdelt_conflict_events_72h": gdelt_count,
        "gdelt_min_goldstein": gdelt_min_goldstein,
        "vix": vix,
        "market_stress": market_stress,
    }


def _build_prompt(country_a: str, country_b: str, ctx: dict) -> str:
    name_a = COUNTRY_NAMES.get(country_a, country_a)
    name_b = COUNTRY_NAMES.get(country_b, country_b)

    # Format sentiment context
    sent_lines = []
    if ctx["sentiment_a"]:
        s = ctx["sentiment_a"]
        sent_lines.append(
            f"  - {name_a}: avg_sentiment={s['avg_sentiment']} (range -1 to +1), "
            f"negative_ratio={s['negative_ratio']}, posts_analyzed={s['post_count']}"
        )
    else:
        sent_lines.append(f"  - {name_a}: no recent tweet data available")

    if ctx["sentiment_b"]:
        s = ctx["sentiment_b"]
        sent_lines.append(
            f"  - {name_b}: avg_sentiment={s['avg_sentiment']} (range -1 to +1), "
            f"negative_ratio={s['negative_ratio']}, posts_analyzed={s['post_count']}"
        )
    else:
        sent_lines.append(f"  - {name_b}: no recent tweet data available")

    sentiment_section = "\n".join(sent_lines)

    gdelt_section = (
        f"GDELT conflict events (last 72h, Goldstein < -5): {ctx['gdelt_conflict_events_72h']}\n"
        f"Most hostile event Goldstein scale: {ctx['gdelt_min_goldstein']}"
        if ctx["gdelt_conflict_events_72h"] > 0
        else "GDELT: No high-conflict events detected in last 72 hours"
    )

    market_section = (
        f"VIX (fear index): {ctx['vix']:.1f}, Market stress score: {ctx['market_stress']:.2f}"
        if ctx["vix"] is not None
        else "Market data: not available"
    )

    today = datetime.utcnow().strftime("%B %d, %Y")

    return f"""You are a senior geopolitical risk analyst at an institutional intelligence firm.
Today's date: {today}

Assess the current bilateral geopolitical risk between {name_a} and {name_b}.

Use your knowledge of the latest geopolitical developments, diplomatic relations,
military postures, economic tensions, and any recent events up to your knowledge cutoff.

Also consider these real-time signals from our monitoring system:

SENTIMENT SIGNALS (from political social media, last 72h):
{sentiment_section}

CONFLICT SIGNALS:
{gdelt_section}

MARKET SIGNALS:
{market_section}

Provide a risk score from 0 to 100 where:
  0-25  = LOW (stable relations, no significant tensions)
  26-50 = MODERATE (some friction, manageable tensions)
  51-75 = HIGH (significant tensions, escalation risk)
  76-100 = CRITICAL (active conflict risk, crisis conditions)

Be realistic and differentiated — not every pair should score 100.
Base your score on actual current geopolitical reality.

Respond ONLY with a valid JSON object (no markdown, no explanation outside JSON):
{{
  "score": <integer 0-100>,
  "classification": "<LOW|MODERATE|HIGH|CRITICAL>",
  "contributing_factors": [
    {{"factor": "<specific reason>", "impact": <float 0.0-0.3>, "category": "<sentiment|political|military|economic|events>"}},
    {{"factor": "<specific reason>", "impact": <float 0.0-0.3>, "category": "<category>"}}
  ],
  "reasoning": "<2-3 sentence analytical justification referencing specific current events>"
}}"""


def _call_groq(prompt: str, groq_api_key: str) -> Optional[dict]:
    """Call Groq API and return parsed JSON response."""
    try:
        from groq import Groq
        client = Groq(api_key=groq_api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=512,
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return None


def score_pair_with_groq(
    country_a: str,
    country_b: str,
    groq_api_key: str,
) -> Optional[RiskScore]:
    """
    Score a single country pair using Groq LLM.
    Writes result to RiskScore table and returns the object.
    """
    pair_key = RiskScore.make_pair_key(country_a, country_b)

    with get_db_session() as db:
        ctx = _get_context(country_a, country_b, db)
        prompt = _build_prompt(country_a, country_b, ctx)

        data = _call_groq(prompt, groq_api_key)
        if data is None:
            logger.warning(f"Groq scoring failed for {pair_key}, skipping")
            return None

        # Validate and clamp score
        score = float(data.get("score", 50))
        score = max(0.0, min(100.0, score))
        classification = RiskScore.classify(score)

        # ── Pinned score override ─────────────────────────────────────────────
        # Always enforce pinned scores regardless of what Groq returns.
        from scoring.risk_calculator import PINNED_SCORES
        if pair_key in PINNED_SCORES:
            pinned = PINNED_SCORES[pair_key]
            if abs(score - pinned) > 0.5:
                logger.info(
                    f"{pair_key}: Groq score {score:.1f} overridden by "
                    f"pinned score {pinned:.1f}"
                )
            score = pinned
            classification = RiskScore.classify(score)

        # Previous score for delta
        prev = db.query(RiskScore).filter_by(pair_key=pair_key).order_by(
            RiskScore.computed_at.desc()
        ).first()
        prev_score_val = prev.score if prev else None
        score_change = round(score - prev_score_val, 2) if prev_score_val is not None else 0.0

        # Build contributing factors — include reasoning as a factor
        factors = data.get("contributing_factors", [])
        reasoning = data.get("reasoning", "")
        if reasoning and not any(f.get("factor") == reasoning for f in factors):
            factors.append({
                "factor": reasoning,
                "impact": round(score / 100 * 0.3, 3),
                "category": "llm_analysis",
            })

        # Derive component scores from context for breakdown display
        sent_a = ctx["sentiment_a"]
        sent_b = ctx["sentiment_b"]
        avg_neg_ratio = 0.5
        if sent_a and sent_b:
            avg_neg_ratio = (sent_a["negative_ratio"] + sent_b["negative_ratio"]) / 2
        elif sent_a:
            avg_neg_ratio = sent_a["negative_ratio"]
        elif sent_b:
            avg_neg_ratio = sent_b["negative_ratio"]

        vix = ctx["vix"] or 18.0
        vix_score = round(min(max((vix - 10) / 40.0, 0.0), 1.0), 4)
        gdelt_score = round(min(ctx["gdelt_conflict_events_72h"] / 10.0, 1.0), 4)
        market_stress = ctx["market_stress"] or 0.0

        risk = RiskScore(
            country_a=country_a.upper(),
            country_b=country_b.upper(),
            pair_key=pair_key,
            score=score,
            classification=classification,
            negative_sentiment_score=round(avg_neg_ratio, 4),
            sentiment_deterioration_rate=0.0,
            politician_hostility_score=round(avg_neg_ratio * 0.8, 4),
            gdelt_conflict_intensity=gdelt_score,
            vix_spike_score=vix_score,
            market_stress_score=round(market_stress, 4),
            window_hours=72,
            post_count_a=(sent_a["post_count"] if sent_a else 0),
            post_count_b=(sent_b["post_count"] if sent_b else 0),
            gdelt_event_count=ctx["gdelt_conflict_events_72h"],
            contributing_factors=factors,
            prev_score=prev_score_val,
            score_change=score_change,
            computed_at=datetime.utcnow(),
        )
        db.add(risk)

        logger.info(
            f"Groq risk score {pair_key}: {score:.1f} ({classification}) "
            f"[Δ{score_change:+.1f}]"
        )
        return risk


class GroqRiskScoreEngine:
    """
    Scores all tracked country pairs using Groq LLM.
    Called by the scheduler every 30 minutes.
    """

    def __init__(self, groq_api_key: str):
        self.groq_api_key = groq_api_key

    def run(self) -> int:
        logger.info("Groq risk score engine starting...")
        computed = 0
        for a, b in TRACKED_PAIRS:
            try:
                result = score_pair_with_groq(a, b, self.groq_api_key)
                if result:
                    computed += 1
            except Exception as e:
                logger.error(f"Groq risk score failed for {a}-{b}: {e}")
        logger.info(f"Groq risk engine done: {computed}/{len(TRACKED_PAIRS)} pairs scored.")
        return computed
