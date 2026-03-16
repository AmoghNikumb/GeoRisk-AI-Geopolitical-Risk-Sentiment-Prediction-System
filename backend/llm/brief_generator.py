import json
import logging
from datetime import datetime
import google.generativeai as genai
from config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

async def generate_intel_brief(pair_key: str, context: dict) -> dict:
    prompt = f"""You are a geopolitical intelligence analyst. Generate a structured intelligence brief.

Context:
- Country Pair: {context.get('pair_key')}
- Risk Score: {context.get('risk_score')} / 100
- Classification: {context.get('classification')}
- Avg Sentiment (Country A): {context.get('sentiment_a')}
- Avg Sentiment (Country B): {context.get('sentiment_b')}
- VIX: {context.get('vix')}
- GDELT Conflict Events: {context.get('gdelt_events')}
- Top Posts Sample: {context.get('top_posts')}

Respond ONLY with a JSON object, no markdown, no explanation:
{{
  "headline": "one sentence headline",
  "risk_level": "LOW|MODERATE|HIGH|CRITICAL",
  "summary": "2-3 sentence situation summary",
  "key_drivers": ["driver 1", "driver 2", "driver 3"],
  "market_implications": "one sentence",
  "outlook_72hr": "one sentence forecast",
  "confidence": 0.0 to 1.0
}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        data["generated_at"] = datetime.utcnow().isoformat()
        return data
    except Exception as e:
        logger.error(f"Gemini brief generation failed: {e}")
        return {
            "headline": f"Risk assessment for {pair_key}",
            "risk_level": context.get("classification", "UNKNOWN"),
            "summary": "Automated brief generation temporarily unavailable.",
            "key_drivers": [],
            "market_implications": None,
            "outlook_72hr": None,
            "confidence": 0.0,
            "generated_at": datetime.utcnow().isoformat(),
        }