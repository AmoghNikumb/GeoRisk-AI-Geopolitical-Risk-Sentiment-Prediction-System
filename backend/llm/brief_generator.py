"""
llm/brief_generator.py
Generates structured intelligence briefs using Claude API.
Called on-demand (user opens bilateral page) or scheduled (every 6hrs).
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Optional

import anthropic

from config import settings
from database import get_db_session
from models.risk_score import RiskScore
from models.intel_brief import IntelBrief
from models.processed_post import ProcessedPost
from models.gdelt_event import GdeltEvent

logger = logging.getLogger(__name__)

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


SYSTEM_PROMPT = """You are a senior geopolitical intelligence analyst. You provide concise, 
factual, structured intelligence briefs based on quantitative data signals. 
Your tone is professional, measured, and analytical — not alarmist.
Always respond ONLY with valid JSON, no markdown, no preamble."""

BRIEF_PROMPT_TEMPLATE = """Analyze the following data signals for the {country_a}–{country_b} bilateral relationship 
and generate a structured intelligence brief.

## Current Risk Indicators
- Risk Score: {risk_score}/100 ({risk_level})
- Score Change (72h): {score_change:+.1f} points
- Sentiment Deterioration Rate: {deterioration_rate:.2f}
- GDELT Conflict Events (72h): {gdelt_events}
- VIX (Fear Index): {vix:.1f}
- Market Stress: {market_stress:.2f}

## Top Contributing Factors
{contributing_factors}

## Recent High-Impact Posts (last 24h)
{top_posts}

## Politicians with Hostile Rhetoric
{politician_posts}

## Recent GDELT Events
{gdelt_summary}

Respond ONLY with this exact JSON structure:
{{
  "headline": "<one concise sentence summarizing the situation>",
  "risk_level": "{risk_level}",
  "summary": "<2-3 paragraph analytical summary of the bilateral situation>",
  "key_drivers": ["<driver 1>", "<driver 2>", "<driver 3>"],
  "market_implications": "<1 paragraph on potential financial/economic impacts>",
  "outlook_72hr": "<1 paragraph near-term prediction for the next 72 hours>",
  "confidence": <0.0-1.0 float representing your confidence in this assessment>
}}"""


class BriefGenerator:
    def __init__(self):
        self.client = _get_client()

    def _get_context(self, country_a: str, country_b: str, risk: RiskScore) -> dict:
        """Gather supporting data for the brief prompt."""
        since = datetime.utcnow() - timedelta(hours=24)

        with get_db_session() as db:
            # Top negative posts
            posts = db.query(ProcessedPost).filter(
                ProcessedPost.mentioned_countries.contains([country_a]) |
                ProcessedPost.mentioned_countries.contains([country_b]),
                ProcessedPost.sentiment_score < -0.3,
                ProcessedPost.posted_at >= since,
            ).order_by(ProcessedPost.sentiment_score.asc()).limit(8).all()

            top_posts_str = "\n".join(
                f"- [{p.source.upper()}] @{p.author}: \"{p.clean_text[:150]}...\""
                for p in posts
            ) or "No recent hostile posts detected."

            # Politician posts
            pol_posts = db.query(ProcessedPost).filter(
                ProcessedPost.source == "twitter",
                ProcessedPost.author_verified == True,  # noqa: E712
                ProcessedPost.sentiment_score < -0.3,
                ProcessedPost.posted_at >= since,
                ProcessedPost.mentioned_countries.contains([country_a]) |
                ProcessedPost.mentioned_countries.contains([country_b]),
            ).order_by(ProcessedPost.influence_weight.desc()).limit(5).all()

            pol_str = "\n".join(
                f"- {p.author} (weight={p.influence_weight:.1f}): \"{p.clean_text[:120]}...\""
                for p in pol_posts
            ) or "No hostile politician posts in last 24h."

            # GDELT events
            gdelt_events = db.query(GdeltEvent).filter(
                GdeltEvent.event_date >= since,
                GdeltEvent.goldstein_scale < -5,
            ).filter(
                (GdeltEvent.actor1_country.in_([country_a, country_b])) |
                (GdeltEvent.actor2_country.in_([country_a, country_b]))
            ).order_by(GdeltEvent.goldstein_scale.asc()).limit(5).all()

            gdelt_str = "\n".join(
                f"- [{e.actor1_country}→{e.actor2_country}] GS={e.goldstein_scale:.1f}: "
                f"{e.event_description or e.event_code} ({e.num_articles} articles)"
                for e in gdelt_events
            ) or "No significant GDELT conflict events in last 24h."

        factors_str = "\n".join(
            f"- {f['factor']} (impact: {f['impact']:.3f})"
            for f in (risk.contributing_factors or [])
        ) or "No specific factors identified."

        return {
            "top_posts": top_posts_str,
            "politician_posts": pol_str,
            "gdelt_summary": gdelt_str,
            "contributing_factors": factors_str,
        }

    def generate(
        self,
        country_a: str,
        country_b: str,
        trigger: str = "on_demand",
        force: bool = False
    ) -> Optional[IntelBrief]:
        """
        Generate or return cached intel brief for a country pair.
        Returns None if generation fails.
        """
        pair_key = RiskScore.make_pair_key(country_a, country_b)

        # Check cache first (unless forced)
        if not force:
            with get_db_session() as db:
                cached = db.query(IntelBrief).filter_by(pair_key=pair_key).order_by(
                    IntelBrief.generated_at.desc()
                ).first()
                if cached and not cached.is_expired():
                    logger.info(f"Returning cached brief for {pair_key}")
                    return cached

        # Get latest risk score
        with get_db_session() as db:
            risk = db.query(RiskScore).filter_by(pair_key=pair_key).order_by(
                RiskScore.computed_at.desc()
            ).first()

        if not risk:
            logger.warning(f"No risk score found for {pair_key}, skipping brief.")
            return None

        context = self._get_context(country_a, country_b, risk)

        prompt = BRIEF_PROMPT_TEMPLATE.format(
            country_a=country_a,
            country_b=country_b,
            risk_score=risk.score,
            risk_level=risk.classification,
            score_change=risk.score_change or 0.0,
            deterioration_rate=risk.sentiment_deterioration_rate or 0.0,
            gdelt_events=risk.gdelt_event_count or 0,
            vix=risk.vix_spike_score * 40 if risk.vix_spike_score else 15.0,
            market_stress=risk.market_stress_score or 0.0,
            **context,
        )

        try:
            logger.info(f"Generating brief for {pair_key}...")
            message = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = message.content[0].text.strip()

            # Strip any accidental markdown
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0]

            parsed = json.loads(raw_text)

            expires = datetime.utcnow() + timedelta(hours=settings.brief_cache_hours)

            brief = IntelBrief(
                country_a=country_a.upper(),
                country_b=country_b.upper(),
                pair_key=pair_key,
                risk_score_id=risk.id,
                risk_score_val=risk.score,
                risk_level=parsed.get("risk_level", risk.classification),
                headline=parsed.get("headline", ""),
                summary=parsed.get("summary", ""),
                key_drivers=parsed.get("key_drivers", []),
                market_implications=parsed.get("market_implications", ""),
                outlook_72hr=parsed.get("outlook_72hr", ""),
                confidence=parsed.get("confidence", 0.5),
                raw_response=parsed,
                trigger=trigger,
                generated_at=datetime.utcnow(),
                expires_at=expires,
            )

            with get_db_session() as db:
                db.add(brief)

            logger.info(f"Brief generated for {pair_key}: {brief.headline[:80]}")
            return brief

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude JSON for {pair_key}: {e}\nRaw: {raw_text[:300]}")
            return None
        except Exception as e:
            logger.error(f"Brief generation failed for {pair_key}: {e}")
            return None

