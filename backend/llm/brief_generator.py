"""
llm/brief_generator.py
──────────────────────
Generates structured intelligence briefs using Google Gemini.
Falls back to a template-based brief if Gemini is unavailable or unconfigured.

BriefGenerator.generate() is synchronous and safe to call from:
  - APScheduler jobs
  - FastAPI background tasks
  - Route handlers (via run_in_executor if needed)
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from config import settings
from database import get_db_session
from models.intel_brief import IntelBrief
from models.risk_score import RiskScore
from models.market_snapshot import MarketSnapshot
from models.sentiment_score import SentimentScore

logger = logging.getLogger(__name__)

# ── Template fallback ─────────────────────────────────────────────────────────

_RISK_SUMMARIES = {
    "CRITICAL": (
        "Geopolitical tensions between {a} and {b} have reached a critical threshold. "
        "Multiple indicators — including hostile political rhetoric, elevated conflict events, "
        "and deteriorating bilateral sentiment — point to a high-probability escalation scenario. "
        "Immediate monitoring and contingency planning are advised."
    ),
    "HIGH": (
        "Relations between {a} and {b} are under significant strain. "
        "Sentiment analysis and GDELT conflict data indicate a sustained deterioration "
        "in bilateral dynamics over the past 72 hours. "
        "Escalation risk remains elevated."
    ),
    "MODERATE": (
        "The {a}–{b} relationship shows moderate stress signals. "
        "While no acute crisis is imminent, negative sentiment trends and "
        "periodic conflict events warrant continued monitoring."
    ),
    "LOW": (
        "Current indicators for {a}–{b} suggest a relatively stable bilateral environment. "
        "Sentiment remains broadly neutral and conflict event frequency is within normal range."
    ),
}

_DRIVERS_BY_LEVEL = {
    "CRITICAL": [
        "Sustained hostile rhetoric from senior political figures",
        "Elevated GDELT conflict event frequency (GoldsteinScale < -7)",
        "Rapid deterioration in public sentiment over 72-hour window",
        "Market stress indicators amplifying geopolitical risk premium",
    ],
    "HIGH": [
        "Negative sentiment trend accelerating across monitored channels",
        "Multiple GDELT conflict events detected in bilateral context",
        "Politician hostility scores above threshold",
    ],
    "MODERATE": [
        "Moderate negative sentiment with periodic spikes",
        "Isolated conflict events without sustained escalation pattern",
        "Market indicators showing mild stress correlation",
    ],
    "LOW": [
        "Sentiment broadly neutral or positive",
        "No significant GDELT conflict events in 72-hour window",
        "Market indicators stable",
    ],
}


def _template_brief(pair_key: str, country_a: str, country_b: str,
                    risk_level: str, risk_score: float) -> dict:
    level = risk_level or "MODERATE"
    a_name = country_a
    b_name = country_b
    return {
        "headline": f"{a_name}–{b_name} Risk Assessment: {level} ({risk_score:.0f}/100)",
        "risk_level": level,
        "summary": _RISK_SUMMARIES.get(level, _RISK_SUMMARIES["MODERATE"]).format(
            a=a_name, b=b_name
        ),
        "key_drivers": _DRIVERS_BY_LEVEL.get(level, _DRIVERS_BY_LEVEL["MODERATE"]),
        "market_implications": (
            f"Elevated {a_name}–{b_name} tensions may affect regional equity markets, "
            "commodity prices, and safe-haven flows."
            if level in ("HIGH", "CRITICAL")
            else f"Current {a_name}–{b_name} risk level has limited direct market implications."
        ),
        "outlook_72hr": (
            "Continued monitoring required. Risk of further escalation remains elevated."
            if level in ("HIGH", "CRITICAL")
            else "Situation expected to remain stable barring new developments."
        ),
        "confidence": 0.55,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ── Gemini call ───────────────────────────────────────────────────────────────

def _call_gemini(pair_key: str, context: dict) -> Optional[dict]:
    """Synchronous Gemini call. Returns parsed dict or None."""
    if not settings.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""You are a senior geopolitical intelligence analyst.
Generate a structured intelligence brief for the following situation.

Country Pair: {context.get('pair_key')}
Risk Score: {context.get('risk_score', 'N/A')} / 100
Classification: {context.get('classification', 'UNKNOWN')}
Avg Sentiment (Country A): {context.get('sentiment_a', 'N/A')}
Avg Sentiment (Country B): {context.get('sentiment_b', 'N/A')}
VIX: {context.get('vix', 'N/A')}
GDELT Conflict Events (72h): {context.get('gdelt_events', 0)}

Respond ONLY with a valid JSON object, no markdown fences:
{{
  "headline": "one concise sentence",
  "risk_level": "LOW|MODERATE|HIGH|CRITICAL",
  "summary": "2-3 sentence analytical summary",
  "key_drivers": ["driver 1", "driver 2", "driver 3"],
  "market_implications": "one sentence",
  "outlook_72hr": "one sentence forecast",
  "confidence": 0.0
}}"""

        response = model.generate_content(prompt)
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        data["generated_at"] = datetime.utcnow().isoformat()
        return data
    except Exception as e:
        logger.error(f"Gemini brief generation failed for {pair_key}: {e}")
        return None


# ── BriefGenerator class ──────────────────────────────────────────────────────

class BriefGenerator:
    """
    Synchronous brief generator.
    Checks cache first, then tries Gemini, falls back to template.
    """

    def generate(
        self,
        country_a: str,
        country_b: str,
        trigger: str = "on_demand",
        force: bool = False,
    ) -> Optional[IntelBrief]:
        pair_key = RiskScore.make_pair_key(country_a, country_b)

        with get_db_session() as db:
            # Check cache
            if not force:
                existing = (
                    db.query(IntelBrief)
                    .filter_by(pair_key=pair_key)
                    .order_by(IntelBrief.generated_at.desc())
                    .first()
                )
                if existing and not existing.is_expired():
                    logger.debug(f"Brief cache hit for {pair_key}")
                    return existing

            # Gather context
            risk = (
                db.query(RiskScore)
                .filter_by(pair_key=pair_key)
                .order_by(RiskScore.computed_at.desc())
                .first()
            )
            market = (
                db.query(MarketSnapshot)
                .order_by(MarketSnapshot.captured_at.desc())
                .first()
            )

            from datetime import timedelta
            since = datetime.utcnow() - timedelta(hours=72)
            sent_a = (
                db.query(SentimentScore)
                .filter(
                    SentimentScore.country_code == country_a,
                    SentimentScore.time_bucket >= since,
                )
                .order_by(SentimentScore.time_bucket.desc())
                .first()
            )
            sent_b = (
                db.query(SentimentScore)
                .filter(
                    SentimentScore.country_code == country_b,
                    SentimentScore.time_bucket >= since,
                )
                .order_by(SentimentScore.time_bucket.desc())
                .first()
            )

            context = {
                "pair_key": pair_key,
                "risk_score": risk.score if risk else None,
                "classification": risk.classification if risk else "UNKNOWN",
                "sentiment_a": sent_a.avg_sentiment if sent_a else None,
                "sentiment_b": sent_b.avg_sentiment if sent_b else None,
                "vix": market.vix if market else None,
                "gdelt_events": risk.gdelt_event_count if risk else 0,
            }

            risk_level = risk.classification if risk else "MODERATE"
            risk_score_val = risk.score if risk else 50.0

            # Try Gemini, fall back to template
            data = _call_gemini(pair_key, context)
            if data is None:
                data = _template_brief(
                    pair_key, country_a, country_b, risk_level, risk_score_val
                )

            # Persist
            brief = IntelBrief(
                country_a=country_a.upper(),
                country_b=country_b.upper(),
                pair_key=pair_key,
                risk_score_id=risk.id if risk else None,
                risk_score_val=risk_score_val,
                risk_level=data.get("risk_level", risk_level),
                headline=data.get("headline"),
                summary=data.get("summary"),
                key_drivers=data.get("key_drivers", []),
                market_implications=data.get("market_implications"),
                outlook_72hr=data.get("outlook_72hr"),
                confidence=data.get("confidence", 0.55),
                raw_response=data,
                trigger=trigger,
                generated_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=settings.brief_cache_hours),
            )
            db.add(brief)
            logger.info(f"Brief generated for {pair_key} via {'gemini' if settings.GEMINI_API_KEY else 'template'}")
            return brief
