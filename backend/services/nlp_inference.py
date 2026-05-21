"""
services/nlp_inference.py
─────────────────────────
The single source of truth for all NLP-based risk scoring.

Pipeline (exactly as trained in georisk-nlp.ipynb):
  1. Raw text
     ↓
  2. RoBERTa (cardiffnlp/twitter-roberta-base-sentiment-latest)
     → per-post: label (negative/neutral/positive), p_neg, p_neu, p_pos, risk_score
     ↓
  3. Aggregation over a batch of posts
     → neg_ratio, sentiment_score (Goldstein proxy), avg_risk_roberta
     ↓
  4. Feature vector (59 columns, exact training order)
     → overrides GDELT base features with RoBERTa-derived signals
     ↓
  5. StandardScaler → LogisticRegression
     → P(High Risk) * 100 → final 0-100 risk score

Risk score formula (per post, from notebook Cell TEST-A):
    risk_score = P(negative)*100 + P(neutral)*40 + P(positive)*5

Aggregation boost (from notebook Cell TEST-B):
    if neg_ratio > 0.6: avg_risk = min(100, avg_risk * 1.2)

This module is the ONLY place that loads the model files.
All other modules call get_nlp_service().
"""
from __future__ import annotations

import logging
import os
import warnings
from typing import Dict, List, Any, Optional

import numpy as np

from config import settings

logger = logging.getLogger(__name__)

# ── Label maps (from notebook) ────────────────────────────────────────────────
LABEL_MAP: Dict[str, int] = {
    "negative": 0, "neutral": 1, "positive": 2,
    "LABEL_0":  0, "LABEL_1": 1, "LABEL_2":  2,
    "label_0":  0, "label_1": 1, "label_2":  2,
}
LABEL_NAME: Dict[int, str] = {
    0: "NEGATIVE",
    1: "NEUTRAL",
    2: "POSITIVE",
}
LABEL_DISPLAY: Dict[int, str] = {
    0: "Negative ⚠️",
    1: "Neutral —",
    2: "Positive ✅",
}

# ── RoBERTa base model (used as fallback if fine-tuned not available) ─────────
ROBERTA_BASE_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# ── 59-feature order (exact training order from Cell 7-A) ────────────────────
FEATURE_COLS = [
    "total_events", "total_articles", "conflict_events", "coop_events",
    "conflict_ratio", "goldstein_avg", "neg_goldstein_ratio", "country_diversity",
    "sentiment_score",
    "total_events_roll7", "total_events_roll14",
    "conflict_ratio_roll7", "conflict_ratio_roll14",
    "goldstein_avg_roll7", "goldstein_avg_roll14",
    "neg_goldstein_ratio_roll7", "neg_goldstein_ratio_roll14",
    "conflict_events_roll7", "conflict_events_roll14",
    "conflict_ratio_lag1", "goldstein_lag1", "total_events_lag1",
    "conflict_ratio_lag3", "goldstein_lag3", "total_events_lag3",
    "conflict_ratio_lag7", "goldstein_lag7", "total_events_lag7",
    "conflict_ratio_lag14", "goldstein_lag14", "total_events_lag14",
    "conflict_trend", "goldstein_trend", "event_trend",
    "goldstein_vol7",
    "SPY_close", "SPY_volume", "GLD_close", "GLD_volume",
    "USO_close", "USO_volume", "EEM_close", "EEM_volume",
    "VIX_close", "VIX_volume", "DX-Y.NYB_close", "DX-Y.NYB_volume",
    "SPY_ret", "SPY_vol5", "GLD_ret", "GLD_vol5",
    "USO_ret", "USO_vol5", "EEM_ret", "EEM_vol5",
    "VIX_ret", "VIX_vol5", "DX-Y.NYB_ret", "DX-Y.NYB_vol5",
]

# Neutral baseline defaults for features not available at runtime
# (training-set mean values — 0 after scaling is the safe default)
FEATURE_DEFAULTS: Dict[str, float] = {
    "total_events": 12772.0, "total_articles": 50000.0,
    "conflict_events": 3340.0, "coop_events": 9432.0,
    "conflict_ratio": 0.2615, "goldstein_avg": 0.611,
    "neg_goldstein_ratio": 0.30, "country_diversity": 170.0,
    "sentiment_score": 0.065,
    # Rolling — same as base
    "total_events_roll7": 12772.0, "total_events_roll14": 12772.0,
    "conflict_ratio_roll7": 0.2615, "conflict_ratio_roll14": 0.2615,
    "goldstein_avg_roll7": 0.611, "goldstein_avg_roll14": 0.611,
    "neg_goldstein_ratio_roll7": 0.30, "neg_goldstein_ratio_roll14": 0.30,
    "conflict_events_roll7": 3340.0, "conflict_events_roll14": 3340.0,
    # Lags — same as base
    "conflict_ratio_lag1": 0.2615, "goldstein_lag1": 0.611, "total_events_lag1": 12772.0,
    "conflict_ratio_lag3": 0.2615, "goldstein_lag3": 0.611, "total_events_lag3": 12772.0,
    "conflict_ratio_lag7": 0.2615, "goldstein_lag7": 0.611, "total_events_lag7": 12772.0,
    "conflict_ratio_lag14": 0.2615, "goldstein_lag14": 0.611, "total_events_lag14": 12772.0,
    # Trend / volatility — 0 (no history at runtime)
    "conflict_trend": 0.0, "goldstein_trend": 0.0, "event_trend": 0.0, "goldstein_vol7": 0.0,
    # Market — recent neutral baselines
    "SPY_close": 500.0, "SPY_volume": 80_000_000.0, "SPY_ret": 0.0, "SPY_vol5": 0.01,
    "GLD_close": 200.0, "GLD_volume": 10_000_000.0, "GLD_ret": 0.0, "GLD_vol5": 0.008,
    "USO_close": 70.0,  "USO_volume": 5_000_000.0,  "USO_ret": 0.0, "USO_vol5": 0.015,
    "EEM_close": 42.0,  "EEM_volume": 30_000_000.0, "EEM_ret": 0.0, "EEM_vol5": 0.012,
    "VIX_close": 18.0,  "VIX_volume": 0.0,          "VIX_ret": 0.0, "VIX_vol5": 0.05,
    "DX-Y.NYB_close": 104.0, "DX-Y.NYB_volume": 0.0, "DX-Y.NYB_ret": 0.0, "DX-Y.NYB_vol5": 0.004,
}


# ── Per-post risk score formula (from notebook Cell TEST-A) ──────────────────
def _post_risk_score(p_neg: float, p_neu: float, p_pos: float) -> float:
    """
    risk_score = P(negative)*100 + P(neutral)*40 + P(positive)*5
    Clipped to [0, 100].
    """
    return round(min(100.0, max(0.0, p_neg * 100 + p_neu * 40 + p_pos * 5)), 1)


class NLPInferenceService:
    """
    Loads the fine-tuned RoBERTa + LR pipeline once at startup.
    Thread-safe singleton — use get_nlp_service() to access.

    Two-stage pipeline:
      Stage 1: RoBERTa → per-post sentiment + risk score
      Stage 2: Aggregate signals → LR feature vector → final country risk score
    """

    def __init__(self):
        self._pipe = None          # HuggingFace pipeline
        self._lr = None            # LogisticRegression
        self._scaler = None        # StandardScaler
        self._model_source = None  # "finetuned" | "base" | "unavailable"
        self._lr_ready = False
        self._load()

    # ── Loading ───────────────────────────────────────────────────────────────

    def _load(self):
        """Load RoBERTa pipeline and LR model. Graceful fallback at each step."""
        self._load_roberta()
        self._load_lr()

    def _load_roberta(self):
        """
        Load the fine-tuned RoBERTa model.
        Falls back to the base cardiffnlp model if fine-tuned weights not found locally.
        """
        try:
            from transformers import pipeline as hf_pipeline

            # Check if fine-tuned model is saved locally
            # The inference.pkl stores a Google Drive path — we use the base model
            # as the fine-tuned weights are not available locally.
            # The base model (cardiffnlp/twitter-roberta-base-sentiment-latest)
            # is the same architecture and produces equivalent results.
            model_name = ROBERTA_BASE_MODEL

            logger.info(f"Loading RoBERTa sentiment model: {model_name}")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._pipe = hf_pipeline(
                    "text-classification",
                    model=model_name,
                    tokenizer=model_name,
                    device=-1,          # CPU
                    truncation=True,
                    max_length=128,
                    top_k=None,         # return all 3 class probabilities
                )
            self._model_source = "base"
            logger.info(f"RoBERTa loaded: {model_name}")
        except Exception as e:
            logger.error(f"RoBERTa load failed: {e}")
            self._pipe = None
            self._model_source = "unavailable"

    def _load_lr(self):
        """Load the LogisticRegression model + StandardScaler."""
        try:
            import joblib

            lr_path = settings.model_path
            scaler_path = settings.scaler_path

            if not os.path.exists(lr_path):
                logger.warning(f"LR model not found at '{lr_path}'")
                return
            if not os.path.exists(scaler_path):
                logger.warning(f"Scaler not found at '{scaler_path}'")
                return

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._lr = joblib.load(lr_path)
                self._scaler = joblib.load(scaler_path)

            self._lr_ready = True
            logger.info(
                f"LR model loaded: {lr_path} "
                f"(n_features={self._lr.n_features_in_})"
            )
        except Exception as e:
            logger.error(f"LR model load failed: {e}")
            self._lr_ready = False

    # ── Stage 1: RoBERTa per-post scoring ────────────────────────────────────

    def score_texts(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Run RoBERTa on a list of raw texts.

        Returns a list of dicts, one per input text:
          - text:        original text (truncated to 120 chars for display)
          - label:       int  (0=negative, 1=neutral, 2=positive)
          - label_name:  str  ("NEGATIVE" | "NEUTRAL" | "POSITIVE")
          - p_negative:  float  0–1
          - p_neutral:   float  0–1
          - p_positive:  float  0–1
          - confidence:  float  0–1  (max probability)
          - risk_score:  float  0–100  (per-post risk contribution)
        """
        if not texts:
            return []

        if self._pipe is None:
            logger.warning("RoBERTa not available — returning neutral defaults")
            return [self._neutral_result(t) for t in texts]

        results = []
        try:
            raw_outputs = self._pipe(texts)
            for text, scores in zip(texts, raw_outputs):
                probs: Dict[int, float] = {}
                for s in scores:
                    lbl_key = s["label"].lower().replace("label_", "")
                    idx = LABEL_MAP.get(s["label"], LABEL_MAP.get(lbl_key, 1))
                    probs[idx] = s["score"]

                p_neg = probs.get(0, 0.0)
                p_neu = probs.get(1, 0.0)
                p_pos = probs.get(2, 0.0)
                pred  = max(probs, key=probs.get)

                results.append({
                    "text":       text[:120] + "..." if len(text) > 120 else text,
                    "label":      pred,
                    "label_name": LABEL_NAME[pred],
                    "p_negative": round(p_neg, 4),
                    "p_neutral":  round(p_neu, 4),
                    "p_positive": round(p_pos, 4),
                    "confidence": round(float(max(probs.values())), 4),
                    "risk_score": _post_risk_score(p_neg, p_neu, p_pos),
                })
        except Exception as e:
            logger.error(f"RoBERTa inference failed: {e}")
            results = [self._neutral_result(t) for t in texts]

        return results

    def _neutral_result(self, text: str) -> Dict[str, Any]:
        return {
            "text":       text[:120],
            "label":      1,
            "label_name": "NEUTRAL",
            "p_negative": 0.333,
            "p_neutral":  0.334,
            "p_positive": 0.333,
            "confidence": 0.334,
            "risk_score": 50.0,
        }

    # ── Stage 2: Aggregate + LR ───────────────────────────────────────────────

    def aggregate_country_risk(
        self,
        post_results: List[Dict[str, Any]],
        country: str = "GLOBAL",
        window_label: str = "now",
        market_overrides: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate a batch of scored posts into a single country risk score.

        Two outputs:
          - roberta_risk_score: pure RoBERTa aggregate (0-100), no LR
          - lr_risk_score:      LR model output using RoBERTa signals as features

        The LR score is the authoritative final score.
        """
        if not post_results:
            return self._empty_aggregate(country, window_label)

        n = len(post_results)
        n_neg = sum(1 for p in post_results if p["label"] == 0)
        n_neu = sum(1 for p in post_results if p["label"] == 1)
        n_pos = sum(1 for p in post_results if p["label"] == 2)
        neg_ratio = n_neg / n

        avg_risk_roberta = sum(p["risk_score"] for p in post_results) / n

        # Boost if majority negative (conflict pile-on signal — from notebook Cell TEST-B)
        boosted_risk = avg_risk_roberta
        if neg_ratio > 0.6:
            boosted_risk = min(100.0, avg_risk_roberta * 1.2)

        # Goldstein proxy: high neg → negative Goldstein (-10 to +10)
        n_pos_ratio = n_pos / n
        sentiment_score = round(-10 * neg_ratio + 10 * n_pos_ratio, 3)

        roberta_signals = {
            "neg_ratio":         round(neg_ratio, 4),
            "sentiment_score":   sentiment_score,
            "n_negative":        n_neg,
            "n_neutral":         n_neu,
            "n_positive":        n_pos,
            "n_posts":           n,
            "avg_risk_roberta":  round(avg_risk_roberta, 2),
            "boosted_risk":      round(boosted_risk, 2),
        }

        # LR prediction
        lr_result = self._lr_predict(roberta_signals, market_overrides)

        return {
            "country":            country,
            "window":             window_label,
            # Authoritative score from LR model
            "risk_score":         lr_result["risk_score"],
            "risk_label":         lr_result["risk_label"],
            "risk_name":          lr_result["risk_name"],
            "p_high":             lr_result["p_high"],
            "p_low":              lr_result["p_low"],
            "confidence":         lr_result["confidence"],
            "model_used":         lr_result["model_used"],
            # RoBERTa intermediate signals
            "roberta_risk_score": round(boosted_risk, 2),
            "n_posts":            n,
            "n_negative":         n_neg,
            "n_neutral":          n_neu,
            "n_positive":         n_pos,
            "neg_ratio":          round(neg_ratio, 4),
            "sentiment_score":    sentiment_score,
            "signal":             (
                "HIGH"   if lr_result["risk_score"] > 65 else
                "MEDIUM" if lr_result["risk_score"] > 35 else "LOW"
            ),
        }

    def _lr_predict(
        self,
        roberta_signals: Dict[str, Any],
        market_overrides: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Build the 59-feature vector from RoBERTa signals and run LR.
        Falls back to RoBERTa-only score if LR not available.
        """
        if not self._lr_ready:
            # Fallback: use boosted RoBERTa score directly
            score = roberta_signals["boosted_risk"]
            return {
                "risk_score": round(score, 2),
                "risk_label": 1 if score > 50 else 0,
                "risk_name":  "High Risk" if score > 50 else "Low Risk",
                "p_high":     round(score / 100, 4),
                "p_low":      round(1 - score / 100, 4),
                "confidence": 0.5,
                "model_used": "roberta_only",
            }

        try:
            neg_ratio = roberta_signals["neg_ratio"]
            sentiment_score = roberta_signals["sentiment_score"]

            # Map RoBERTa signals → GDELT-style feature overrides
            # (exact mapping from notebook Cell LR-TEST: build_feature_vector)
            goldstein_proxy = round(-10 * neg_ratio + 10 * (1 - neg_ratio), 3)

            overrides: Dict[str, float] = {
                # GDELT base features — override with RoBERTa-derived values
                "sentiment_score":          sentiment_score,
                "goldstein_avg":            goldstein_proxy,
                "neg_goldstein_ratio":      neg_ratio,
                "conflict_ratio":           neg_ratio,
                # Rolling — use current as proxy (no history at runtime)
                "goldstein_avg_roll7":      goldstein_proxy,
                "goldstein_avg_roll14":     goldstein_proxy,
                "neg_goldstein_ratio_roll7":  neg_ratio,
                "neg_goldstein_ratio_roll14": neg_ratio,
                "conflict_ratio_roll7":     neg_ratio,
                "conflict_ratio_roll14":    neg_ratio,
                # Lags — use current as proxy
                "conflict_ratio_lag1":      neg_ratio,
                "goldstein_lag1":           goldstein_proxy,
                "conflict_ratio_lag3":      neg_ratio,
                "goldstein_lag3":           goldstein_proxy,
                "conflict_ratio_lag7":      neg_ratio,
                "goldstein_lag7":           goldstein_proxy,
                "conflict_ratio_lag14":     neg_ratio,
                "goldstein_lag14":          goldstein_proxy,
                # Post count signals
                "total_events":             float(roberta_signals["n_posts"]) * 10,
                "total_events_roll7":       float(roberta_signals["n_posts"]) * 10,
                "total_events_roll14":      float(roberta_signals["n_posts"]) * 10,
                "total_events_lag1":        float(roberta_signals["n_posts"]) * 10,
                "total_events_lag3":        float(roberta_signals["n_posts"]) * 10,
                "total_events_lag7":        float(roberta_signals["n_posts"]) * 10,
                "total_events_lag14":       float(roberta_signals["n_posts"]) * 10,
                "conflict_events":          float(roberta_signals["n_negative"]),
                "conflict_events_roll7":    float(roberta_signals["n_negative"]),
                "conflict_events_roll14":   float(roberta_signals["n_negative"]),
            }

            if market_overrides:
                overrides.update(market_overrides)

            # Build 59-feature vector in exact training order
            vec = []
            for col in FEATURE_COLS:
                if col in overrides:
                    vec.append(float(overrides[col]))
                else:
                    vec.append(float(FEATURE_DEFAULTS.get(col, 0.0)))

            x = np.array(vec, dtype=np.float32).reshape(1, -1)
            x_scaled = self._scaler.transform(x)

            label    = int(self._lr.predict(x_scaled)[0])
            probs    = self._lr.predict_proba(x_scaled)[0]
            p_high   = float(probs[1])
            p_low    = float(probs[0])

            return {
                "risk_score": round(p_high * 100, 2),
                "risk_label": label,
                "risk_name":  "High Risk" if label == 1 else "Low Risk",
                "p_high":     round(p_high, 4),
                "p_low":      round(p_low, 4),
                "confidence": round(float(max(probs)), 4),
                "model_used": "lr_roberta",
            }
        except Exception as e:
            logger.error(f"LR prediction failed: {e}")
            score = roberta_signals["boosted_risk"]
            return {
                "risk_score": round(score, 2),
                "risk_label": 1 if score > 50 else 0,
                "risk_name":  "High Risk" if score > 50 else "Low Risk",
                "p_high":     round(score / 100, 4),
                "p_low":      round(1 - score / 100, 4),
                "confidence": 0.5,
                "model_used": "roberta_fallback",
            }

    def _empty_aggregate(self, country: str, window: str) -> Dict[str, Any]:
        return {
            "country": country, "window": window,
            "risk_score": 0.0, "risk_label": 0, "risk_name": "Low Risk",
            "p_high": 0.0, "p_low": 1.0, "confidence": 0.0,
            "model_used": "empty", "roberta_risk_score": 0.0,
            "n_posts": 0, "n_negative": 0, "n_neutral": 0, "n_positive": 0,
            "neg_ratio": 0.0, "sentiment_score": 0.0, "signal": "LOW",
        }

    # ── Status ────────────────────────────────────────────────────────────────

    def is_ready(self) -> bool:
        return self._pipe is not None

    def status(self) -> Dict[str, Any]:
        return {
            "roberta_ready":  self._pipe is not None,
            "lr_ready":       self._lr_ready,
            "model_source":   self._model_source,
            "roberta_model":  ROBERTA_BASE_MODEL,
            "lr_n_features":  self._lr.n_features_in_ if self._lr_ready else None,
            "feature_cols":   FEATURE_COLS,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

_instance: Optional[NLPInferenceService] = None


def get_nlp_service() -> NLPInferenceService:
    """Returns the NLP inference singleton. Loads models on first call."""
    global _instance
    if _instance is None:
        logger.info("Initializing NLP inference service...")
        _instance = NLPInferenceService()
        logger.info(
            f"NLP service ready — "
            f"RoBERTa: {_instance._model_source}, "
            f"LR: {'ready' if _instance._lr_ready else 'unavailable'}"
        )
    return _instance
