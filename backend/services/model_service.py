"""
services/model_service.py
─────────────────────────
Model service abstraction layer.

Phase 1 (now):   DummyModelService — rule-based deterministic scoring.
Phase 2 (later): PickleModelService — load exported .pkl from Jupyter.

To switch to .pkl:
  1. Place your model file at the path in settings.model_path
  2. Set MODEL_BACKEND=pickle in .env
  3. The PickleModelService will load it automatically on first call.

The feature vector shape must match what build_features() returns.
"""
from __future__ import annotations

import logging
import os
import pickle
from abc import ABC, abstractmethod
from typing import Dict, Any

from config import settings

logger = logging.getLogger(__name__)


# ── Abstract interface ────────────────────────────────────────────────────────

class BaseModelService(ABC):
    """All model backends must implement this interface."""

    @abstractmethod
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Given a feature dict (from feature_builder.build_features),
        return a prediction dict with at minimum:
          - predicted_score: float  (0–100)
          - confidence: float       (0–1)
          - model_backend: str
        """
        ...

    @abstractmethod
    def is_ready(self) -> bool:
        """Returns True if the model is loaded and ready."""
        ...


# ── Dummy (rule-based) implementation ────────────────────────────────────────

class DummyModelService(BaseModelService):
    """
    Rule-based placeholder that mirrors the weighted formula in risk_calculator.py.
    Produces realistic outputs without any ML model.
    Used in Phase 1 and as a fallback.
    """

    def is_ready(self) -> bool:
        return True

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        # Replicate the weighted formula
        w = {
            "negative_sentiment":    settings.weight_negative_sentiment,
            "sentiment_deterioration": settings.weight_sentiment_deterioration,
            "politician_hostility":  settings.weight_politician_hostility,
            "gdelt_conflict":        settings.weight_gdelt_conflict,
            "vix_spike":             settings.weight_vix_spike,
            "market_stress":         settings.weight_market_stress,
        }

        def norm_sent(s: float) -> float:
            return round((1.0 - s) / 2.0, 4)

        def norm_vix(v: float) -> float:
            return round(min(max((v - 10) / 40.0, 0.0), 1.0), 4)

        def norm_gdelt(count: int, gs: float) -> float:
            ev = min(count / 20.0, 1.0)
            gn = min(abs(gs) / 10.0, 1.0) if gs < 0 else 0.0
            return round(ev * 0.5 + gn * 0.5, 4)

        components = {
            "negative_sentiment":    norm_sent(features.get("combined_avg_sentiment", 0.0)),
            "sentiment_deterioration": min(features.get("sentiment_deterioration_rate", 0.0), 1.0),
            "politician_hostility":  norm_sent(features.get("combined_politician_hostility", 0.0)),
            "gdelt_conflict":        norm_gdelt(
                features.get("gdelt_event_count", 0),
                features.get("gdelt_min_goldstein", 0.0),
            ),
            "vix_spike":   norm_vix(features.get("vix", 15.0)),
            "market_stress": features.get("market_stress_score", 0.0),
        }

        raw = sum(w[k] * v for k, v in components.items()) * 100
        score = round(min(max(raw, 0.0), 100.0), 2)

        # Confidence based on data availability
        post_count = features.get("post_count_a", 0) + features.get("post_count_b", 0)
        confidence = round(min(post_count / 100.0, 1.0), 3)

        return {
            "predicted_score": score,
            "confidence": confidence,
            "model_backend": "dummy",
            "components": components,
        }


# ── Pickle implementation (Phase 2) ──────────────────────────────────────────

class PickleModelService(BaseModelService):
    """
    Loads a scikit-learn / XGBoost / any pickle-serialized model.

    TODO (Phase 2):
      - Ensure your Jupyter-exported model accepts a flat feature dict
        or a numpy array in the same order as FEATURE_ORDER below.
      - Update FEATURE_ORDER to match your training feature columns.
      - Set MODEL_BACKEND=pickle and MODEL_PATH=path/to/model.pkl in .env
    """

    # TODO: Update this list to match your training feature columns exactly
    FEATURE_ORDER = [
        "combined_avg_sentiment",
        "sentiment_deterioration_rate",
        "combined_politician_hostility",
        "gdelt_event_count",
        "gdelt_min_goldstein",
        "vix",
        "market_stress_score",
        "post_count_a",
        "post_count_b",
        "negative_ratio_a",
        "negative_ratio_b",
        "volume_spike_a",
        "volume_spike_b",
    ]

    def __init__(self):
        self._model = None
        self._load()

    def _load(self):
        path = settings.model_path
        if not os.path.exists(path):
            logger.warning(
                f"PickleModelService: model file not found at '{path}'. "
                "Falling back to DummyModelService."
            )
            return
        try:
            with open(path, "rb") as f:
                self._model = pickle.load(f)
            logger.info(f"PickleModelService: loaded model from '{path}'")
        except Exception as e:
            logger.error(f"PickleModelService: failed to load model: {e}")

    def is_ready(self) -> bool:
        return self._model is not None

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_ready():
            # Graceful fallback
            logger.warning("PickleModelService not ready — falling back to DummyModelService")
            return DummyModelService().predict(features)

        try:
            import numpy as np
            feature_vector = np.array(
                [features.get(k, 0.0) for k in self.FEATURE_ORDER],
                dtype=float,
            ).reshape(1, -1)

            raw = self._model.predict(feature_vector)[0]
            score = round(float(min(max(raw, 0.0), 100.0)), 2)

            # Confidence from model if it supports predict_proba
            confidence = 0.75
            if hasattr(self._model, "predict_proba"):
                proba = self._model.predict_proba(feature_vector)[0]
                confidence = round(float(max(proba)), 3)

            return {
                "predicted_score": score,
                "confidence": confidence,
                "model_backend": "pickle",
                "components": {},
            }
        except Exception as e:
            logger.error(f"PickleModelService.predict() failed: {e}")
            return DummyModelService().predict(features)


# ── Factory ───────────────────────────────────────────────────────────────────

_instance: BaseModelService | None = None


def get_model_service() -> BaseModelService:
    """
    Returns the configured model service singleton.
    Controlled by settings.model_backend ("dummy" | "pickle").
    """
    global _instance
    if _instance is None:
        if settings.model_backend == "pickle":
            svc = PickleModelService()
            _instance = svc if svc.is_ready() else DummyModelService()
        else:
            _instance = DummyModelService()
        logger.info(f"ModelService initialized: {type(_instance).__name__}")
    return _instance
