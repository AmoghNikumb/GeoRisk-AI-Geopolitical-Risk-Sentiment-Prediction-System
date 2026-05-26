"""
routes/model.py
───────────────
Model inference and demo endpoints.

Endpoints:
  POST /api/model/predict          — GDELT-feature-based LR prediction (legacy)
  POST /api/model/infer            — Direct text → RoBERTa → LR pipeline
  GET  /api/model/demo             — 5 validation sentences scored by model
  GET  /api/model/demo-tweets      — Demo collected posts scored by model
  GET  /api/model/demo-tweets/{pair} — Demo posts for a specific pair
  GET  /api/model/status           — Model backend status
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from services.model_service import get_model_service
from services.nlp_inference import get_nlp_service
from scoring.feature_builder import build_features
from scoring.demo_dataset import (
    score_demo_posts,
    score_validation_sentences,
    get_demo_posts,
    _POST_POOL as DEMO_POSTS,
)
from models.risk_score import RiskScore

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────────

class PredictRequest(BaseModel):
    country_a: str
    country_b: str


class InferRequest(BaseModel):
    texts: List[str]
    country: Optional[str] = "GLOBAL"
    window_label: Optional[str] = "now"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/model/predict")
def predict_risk(req: PredictRequest, db: Session = Depends(get_db)):
    """
    Predict risk score for a country pair using GDELT features + LR model.
    This is the pipeline used by the scheduler (feature_builder → model_service).
    """
    a = req.country_a.upper()
    b = req.country_b.upper()
    pair_key = RiskScore.make_pair_key(a, b)

    try:
        features = build_features(a, b, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature extraction failed: {e}")

    svc = get_model_service()
    result = svc.predict(features)

    return {
        "pair_key":        pair_key,
        "country_a":       a,
        "country_b":       b,
        "predicted_score": result["predicted_score"],
        "classification":  RiskScore.classify(result["predicted_score"]),
        "confidence":      result["confidence"],
        "model_backend":   result["model_backend"],
        "components":      result.get("components", {}),
        "predicted_at":    datetime.utcnow().isoformat(),
        "pipeline":        "gdelt_features → lr_model",
    }


@router.post("/model/infer")
def infer_texts(req: InferRequest):
    """
    Direct text inference endpoint.
    Pipeline: raw texts → RoBERTa → per-post scores → LR aggregate.

    Input:
      texts: list of raw text strings
      country: optional country label for the aggregate
      window_label: optional label for the time window

    Output:
      per_post: list of per-text scores (label, confidence, risk_score, probabilities)
      aggregate: country-level risk score from LR model
      pipeline: description of the inference chain
    """
    if not req.texts:
        raise HTTPException(status_code=400, detail="texts list cannot be empty")
    if len(req.texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per request")

    svc = get_nlp_service()

    per_post = svc.score_texts(req.texts)
    aggregate = svc.aggregate_country_risk(
        per_post,
        country=req.country or "GLOBAL",
        window_label=req.window_label or "now",
    )

    return {
        "country":     req.country,
        "n_texts":     len(req.texts),
        "per_post":    per_post,
        "aggregate":   aggregate,
        "pipeline":    "text → roberta_sentiment → lr_risk_model",
        "inferred_at": datetime.utcnow().isoformat(),
    }


@router.get("/model/demo")
def demo_validation():
    """
    Score the 5 validation sentences through the full NLP pipeline.
    Used to verify model behavior in the UI and backend logs.

    Sentences:
      1. "Airstrikes near the border have increased fears of a broader regional war."
      2. "Officials from both countries agreed to resume peace talks next week."
      3. "Heavy shelling displaced hundreds of civilians overnight."
      4. "The ceasefire appears to be holding in major cities."
      5. "Military mobilization and threats from both sides are escalating tensions."
    """
    try:
        results = score_validation_sentences()
        svc = get_nlp_service()

        # Log results for backend verification
        logger.info("=== DEMO VALIDATION SENTENCES ===")
        for r in results:
            status = "✅" if r["correct"] else "❌"
            logger.info(
                f"  {status} [{r['risk_score']:5.1f}] {r['label_name']:<8} "
                f"(expected {r['expected']}) | {r['text'][:60]}"
            )

        correct_count = sum(1 for r in results if r["correct"])
        return {
            "demo_type":     "validation_sentences",
            "description":   "5 manually defined sentences for model behavior verification",
            "results":       results,
            "summary": {
                "total":          len(results),
                "correct":        correct_count,
                "accuracy":       round(correct_count / len(results), 2),
                "avg_risk_score": round(sum(r["risk_score"] for r in results) / len(results), 1),
            },
            "model_status":  svc.status(),
            "scored_at":     datetime.utcnow().isoformat(),
            "data_note":     "Model validation only — not real-time data",
        }
    except Exception as e:
        logger.error(f"Demo validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/demo-tweets")
def demo_tweets_all():
    """
    Score all demo collected posts through the full NLP pipeline.
    Returns per-post scores + aggregate risk per country pair.

    Data source: Manually curated recent posts (May 2025).
    Clearly labeled as demo_collected — NOT live social intelligence.
    """
    try:
        results = score_demo_posts()

        # Log summary
        logger.info("=== DEMO TWEET SCORING COMPLETE ===")
        for pair_key, data in results.items():
            agg = data["aggregate"]
            logger.info(
                f"  {pair_key}: score={agg['risk_score']:.1f} "
                f"({agg['risk_name']}) | "
                f"n={agg['n_posts']} posts | "
                f"neg_ratio={agg['neg_ratio']:.1%} | "
                f"model={agg['model_used']}"
            )

        return {
            "demo_type":   "collected_posts",
            "description": "Temporary collected posts for model validation (May 2025)",
            "pairs":       results,
            "total_posts": sum(len(v["posts"]) for v in results.values()),
            "scored_at":   datetime.utcnow().isoformat(),
            "data_note":   (
                "⚠️ DEMO DATA — Temporary collected posts (May 2025). "
                "Not live social intelligence. "
                "Live Twitter/X fetching will replace this module."
            ),
        }
    except Exception as e:
        logger.error(f"Demo tweet scoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/demo-tweets/{pair_key}")
def demo_tweets_pair(pair_key: str):
    """
    Score demo posts for a specific country pair.
    pair_key: e.g. "IN-PK", "RU-UA", "IL-IR", "CN-TW", "CN-US", "KP-US"
    """
    pair_key = pair_key.upper()
    try:
        results = score_demo_posts(pair=pair_key)
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No demo posts found for pair '{pair_key}'. "
                       f"Available: IN-PK, RU-UA, IL-IR, CN-TW, CN-US, KP-US"
            )

        pair_data = results.get(pair_key)
        if not pair_data:
            raise HTTPException(status_code=404, detail=f"Pair '{pair_key}' not found in results")

        return {
            "demo_type":   "collected_posts",
            "pair_key":    pair_key,
            "data":        pair_data,
            "scored_at":   datetime.utcnow().isoformat(),
            "data_note":   (
                "⚠️ DEMO DATA — Temporary collected posts (May 2025). "
                "Not live social intelligence."
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Demo tweet scoring failed for {pair_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/status")
def model_status():
    """Returns the current model backend status for both pipelines."""
    from config import settings

    # GDELT-feature LR pipeline
    gdelt_svc = get_model_service()

    # NLP inference pipeline
    nlp_svc = get_nlp_service()
    nlp_status = nlp_svc.status()

    return {
        "gdelt_pipeline": {
            "backend":     settings.model_backend,
            "is_ready":    gdelt_svc.is_ready(),
            "model_class": type(gdelt_svc).__name__,
            "model_path":  settings.model_path,
            "scaler_path": settings.scaler_path,
            "description": "GDELT daily features → StandardScaler → LogisticRegression",
            "model_info": {
                "type":       "LogisticRegression",
                "n_features": 59,
                "output":     "P(High Risk) * 100 → 0-100",
                "labels":     {"0": "Low Risk", "1": "High Risk"},
                "trained_on": "GDELT MASTERREDUCEDV2 1979-2013",
                "accuracy":   0.9282,
                "f1_macro":   0.9071,
            },
        },
        "nlp_pipeline": {
            "roberta_ready":  nlp_status["roberta_ready"],
            "lr_ready":       nlp_status["lr_ready"],
            "model_source":   nlp_status["model_source"],
            "roberta_model":  nlp_status["roberta_model"],
            "lr_n_features":  nlp_status["lr_n_features"],
            "description":    "Raw text → RoBERTa sentiment → feature vector → LR risk score",
            "pipeline_steps": [
                "1. Text preprocessing (truncate to 128 tokens)",
                "2. RoBERTa: P(negative), P(neutral), P(positive)",
                "3. Per-post risk score: P(neg)*100 + P(neu)*40 + P(pos)*5",
                "4. Aggregate: neg_ratio, sentiment_score (Goldstein proxy)",
                "5. Build 59-feature vector with RoBERTa overrides",
                "6. StandardScaler → LogisticRegression → P(High Risk)*100",
            ],
        },
        "checked_at": datetime.utcnow().isoformat(),
    }


@router.get("/model/political-statements")
def political_statements(limit: int = 30, force_reload: bool = False):
    """
    Returns recent political tweets from dataset leaders, scored by our
    RoBERTa model. Each tweet includes:
      - leader info (name, title, country, profile picture)
      - tweet text, date, engagement
      - sentiment label + risk score from our pkl model
      - affected countries detected in the text
      - intel summary generated by Groq LLM (single batched call, or template fallback)

    This powers the "Top Political Statements" section on the dashboard.
    Focuses on key geopolitical actors: Israel, Iran, USA, UK, India, China, Russia, Ukraine.
    """
    from services.knowledge_base import get_knowledge_base, COUNTRY_NAMES
    from config import settings as _settings

    # Priority countries to focus on
    PRIORITY_COUNTRIES = {"IL", "IR", "US", "GB", "IN", "CN", "RU", "UA"}

    try:
        kb = get_knowledge_base(force_reload=force_reload)
        nlp_svc = get_nlp_service()

        # ── Step 1: collect all tweets and score them with RoBERTa ───────────
        raw_statements = []
        for leader in kb["leaders"]:
            # Focus on priority countries
            if leader["country_code"] not in PRIORITY_COUNTRIES:
                continue
                
            for tweet in leader["tweets"][:limit]:
                text = tweet["text"]
                if nlp_svc.is_ready():
                    results = nlp_svc.score_texts([text])
                    r = results[0] if results else None
                else:
                    r = None

                if r:
                    label_name = r["label_name"]
                    risk_score = round(r["risk_score"], 1)
                    p_negative = round(r["p_negative"], 4)
                    p_neutral  = round(r["p_neutral"], 4)
                    p_positive = round(r["p_positive"], 4)
                    confidence = round(r["confidence"], 4)
                    model_used = "roberta_pkl"
                else:
                    label_name = "NEUTRAL"
                    risk_score = 50.0
                    p_negative = 0.333
                    p_neutral  = 0.334
                    p_positive = 0.333
                    confidence = 0.334
                    model_used = "fallback"

                affected_codes = tweet.get("affected_countries", [])
                affected_names = [COUNTRY_NAMES.get(c, c) for c in affected_codes]

                raw_statements.append({
                    "leader": {
                        "username":        leader["username"],
                        "name":            leader["name"],
                        "title":           leader["title"],
                        "country":         leader["country"],
                        "country_code":    leader["country_code"],
                        "profile_picture": leader["profile_picture"],
                    },
                    "tweet": {
                        "id":            tweet["id"],
                        "text":          text,
                        "created_at":    tweet["created_at"],
                        "url":           tweet["url"],
                        "like_count":    tweet["like_count"],
                        "retweet_count": tweet["retweet_count"],
                        "view_count":    tweet["view_count"],
                    },
                    "analysis": {
                        "label":              label_name,
                        "risk_score":         risk_score,
                        "p_negative":         p_negative,
                        "p_neutral":          p_neutral,
                        "p_positive":         p_positive,
                        "confidence":         confidence,
                        "model_used":         model_used,
                        "affected_countries": affected_codes,
                        "affected_names":     affected_names,
                        "intel_summary":      "",  # filled below
                    },
                })

        # Sort by risk score so we show the most relevant ones first
        raw_statements.sort(key=lambda x: x["analysis"]["risk_score"], reverse=True)
        top = raw_statements[:limit]

        # ── Step 2: generate intel summaries in ONE batched Groq call ────────
        summaries = _generate_batch_intel(top, _settings.GROQ_API_KEY)
        for i, stmt in enumerate(top):
            stmt["analysis"]["intel_summary"] = summaries[i]

        return {
            "statements":  top,
            "total":       len(raw_statements),
            "leaders":     len(kb["leaders"]),
            "model_ready": nlp_svc.is_ready(),
            "scored_at":   datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Political statements endpoint failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _generate_batch_intel(statements: list, groq_api_key: str) -> list[str]:
    """
    Generate intel summaries for all statements in a SINGLE Groq API call.
    Returns a list of summary strings in the same order as input.
    Falls back to template summaries if Groq fails or key is missing.
    """
    # Build template fallbacks first — used if Groq fails
    def template(s: dict) -> str:
        label = s["analysis"]["label"]
        score = s["analysis"]["risk_score"]
        name  = s["leader"]["name"]
        countries = ", ".join(s["analysis"]["affected_names"][:3]) or s["leader"]["country"]
        sentiment_word = {"NEGATIVE": "hostile", "POSITIVE": "constructive", "NEUTRAL": "measured"}.get(label, "measured")
        return (
            f"{name} issued a {sentiment_word} statement touching on {countries}. "
            f"Risk assessment: {score:.0f}/100 ({label.lower()} sentiment)."
        )

    fallbacks = [template(s) for s in statements]

    if not groq_api_key or not statements:
        return fallbacks

    try:
        from groq import Groq
        client = Groq(api_key=groq_api_key)

        # Build a single prompt with all tweets numbered
        items = []
        for i, s in enumerate(statements, 1):
            text = s["tweet"]["text"][:200]
            name = s["leader"]["name"]
            country = s["leader"]["country"]
            label = s["analysis"]["label"]
            score = s["analysis"]["risk_score"]
            countries = ", ".join(s["analysis"]["affected_names"][:3]) or country
            items.append(
                f"{i}. [{name}, {country}] Sentiment={label}, Risk={score:.0f}/100, "
                f"Countries={countries}\n   Tweet: \"{text}\""
            )

        prompt = (
            "You are a geopolitical intelligence analyst. For each numbered tweet below, "
            "write exactly ONE sentence of intelligence analysis (max 25 words). "
            "Be specific about geopolitical implications. "
            "Respond with ONLY a JSON array of strings, one per tweet, in the same order.\n\n"
            + "\n".join(items)
            + "\n\nJSON array response:"
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )
        text = response.choices[0].message.content.strip()

        # Parse JSON array
        import json as _json
        # Strip markdown fences if present
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        summaries = _json.loads(text.strip())

        if isinstance(summaries, list) and len(summaries) == len(statements):
            return [str(s).strip() or fallbacks[i] for i, s in enumerate(summaries)]
        return fallbacks

    except Exception as e:
        logger.debug(f"Groq batch intel failed: {e}")
        return fallbacks
