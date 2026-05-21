"""
services/model_service.py
─────────────────────────
Model service abstraction layer.

Phase 1 (now):   DummyModelService — rule-based deterministic scoring.
Phase 2 (active): PickleModelService — loads georisk_lr.pkl + georisk_lr_scaler.pkl

Model details (from georisk-nlp.ipynb):
  - Type: LogisticRegression (scikit-learn 1.6.1)
  - Features: 59 columns (GDELT daily aggregates + rolling/lag/trend + stock market)
  - Output: binary classification — 0=Low Risk, 1=High Risk
  - Scaler: StandardScaler applied before inference (georisk_lr_scaler.pkl)
  - Labels: {0: 'Low Risk', 1: 'High Risk'}
  - Risk score: P(High Risk) * 100  →  0–100

To activate:
  Set MODEL_BACKEND=pickle in .env
  MODEL_PATH=models/georisk_lr.pkl
  SCALER_PATH=models/georisk_lr_scaler.pkl
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


# ── Pickle implementation (georisk_lr.pkl + georisk_lr_scaler.pkl) ───────────

class PickleModelService(BaseModelService):
    """
    Loads georisk_lr.pkl (LogisticRegression) + georisk_lr_scaler.pkl (StandardScaler).

    Trained in georisk-nlp.ipynb on GDELT 1979-2013 daily aggregates.
    Input:  59-feature vector (GDELT rolling/lag/trend + stock market signals)
    Output: P(High Risk) * 100  →  0–100 risk score
    Labels: 0 = Low Risk, 1 = High Risk

    Feature order must exactly match the training order from Cell 7-A of the notebook.
    The scaler MUST be applied before passing features to the model.
    """

    # Exact 59-feature order from Cell 7-A of georisk-nlp.ipynb
    # EXCLUDE_COLS = {date, date_day, risk_label, sentiment}
    # All remaining numeric columns in the order pandas produces them
    FEATURE_ORDER = [
        # ── GDELT base features (Cell 2-B / 5-A / 5-B) ──────────────────────
        "total_events",
        "total_articles",
        "conflict_events",
        "coop_events",
        "conflict_ratio",
        "goldstein_avg",
        "neg_goldstein_ratio",
        "country_diversity",
        "sentiment_score",          # derived from goldstein in Cell 5-B
        # ── Rolling averages (Cell 6-A) ──────────────────────────────────────
        "total_events_roll7",
        "total_events_roll14",
        "conflict_ratio_roll7",
        "conflict_ratio_roll14",
        "goldstein_avg_roll7",
        "goldstein_avg_roll14",
        "neg_goldstein_ratio_roll7",
        "neg_goldstein_ratio_roll14",
        "conflict_events_roll7",
        "conflict_events_roll14",
        # ── Lag features (Cell 6-A) ───────────────────────────────────────────
        "conflict_ratio_lag1",
        "goldstein_lag1",
        "total_events_lag1",
        "conflict_ratio_lag3",
        "goldstein_lag3",
        "total_events_lag3",
        "conflict_ratio_lag7",
        "goldstein_lag7",
        "total_events_lag7",
        "conflict_ratio_lag14",
        "goldstein_lag14",
        "total_events_lag14",
        # ── Trend features (Cell 6-A) ─────────────────────────────────────────
        "conflict_trend",
        "goldstein_trend",
        "event_trend",
        # ── Volatility (Cell 6-A) ─────────────────────────────────────────────
        "goldstein_vol7",
        # ── Stock market features (Cell 6-B, yfinance) ───────────────────────
        "SPY_close",
        "SPY_volume",
        "SPY_ret",
        "SPY_vol5",
        "GLD_close",
        "GLD_volume",
        "GLD_ret",
        "GLD_vol5",
        "USO_close",
        "USO_volume",
        "USO_ret",
        "USO_vol5",
        "EEM_close",
        "EEM_volume",
        "EEM_ret",
        "EEM_vol5",
        "VIX_close",
        "VIX_volume",
        "VIX_ret",
        "VIX_vol5",
        "DX-Y.NYB_close",
        "DX-Y.NYB_volume",
        "DX-Y.NYB_ret",
        "DX-Y.NYB_vol5",
    ]

    # Sensible defaults for features we can't compute at runtime
    # (stock market values — use recent typical values as neutral baseline)
    FEATURE_DEFAULTS = {
        "SPY_close": 500.0,   "SPY_volume": 80_000_000.0,  "SPY_ret": 0.0,   "SPY_vol5": 0.01,
        "GLD_close": 200.0,   "GLD_volume": 10_000_000.0,  "GLD_ret": 0.0,   "GLD_vol5": 0.008,
        "USO_close": 70.0,    "USO_volume": 5_000_000.0,   "USO_ret": 0.0,   "USO_vol5": 0.015,
        "EEM_close": 42.0,    "EEM_volume": 30_000_000.0,  "EEM_ret": 0.0,   "EEM_vol5": 0.012,
        "VIX_close": 18.0,    "VIX_volume": 0.0,           "VIX_ret": 0.0,   "VIX_vol5": 0.05,
        "DX-Y.NYB_close": 104.0, "DX-Y.NYB_volume": 0.0,  "DX-Y.NYB_ret": 0.0, "DX-Y.NYB_vol5": 0.004,
        # GDELT defaults (neutral/average day)
        "total_events": 5000.0,
        "total_articles": 20000.0,
        "conflict_events": 1200.0,
        "coop_events": 3600.0,
        "conflict_ratio": 0.26,
        "goldstein_avg": 0.65,
        "neg_goldstein_ratio": 0.30,
        "country_diversity": 170.0,
        "sentiment_score": 0.065,
    }

    def __init__(self):
        self._model = None
        self._scaler = None
        self._load()

    def _load(self):
        import joblib

        model_path = settings.model_path
        scaler_path = settings.scaler_path

        # Load model
        if not os.path.exists(model_path):
            logger.warning(
                f"PickleModelService: model not found at '{model_path}'. "
                "Falling back to DummyModelService."
            )
            return
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._model = joblib.load(model_path)
            logger.info(f"PickleModelService: loaded model from '{model_path}'")
        except Exception as e:
            logger.error(f"PickleModelService: failed to load model: {e}")
            return

        # Load scaler (required — model was trained on scaled features)
        if not os.path.exists(scaler_path):
            logger.warning(
                f"PickleModelService: scaler not found at '{scaler_path}'. "
                "Predictions will be unreliable without scaling."
            )
        else:
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self._scaler = joblib.load(scaler_path)
                logger.info(f"PickleModelService: loaded scaler from '{scaler_path}'")
            except Exception as e:
                logger.error(f"PickleModelService: failed to load scaler: {e}")

    def is_ready(self) -> bool:
        return self._model is not None

    def _build_feature_vector(self, features: Dict[str, Any]):
        """
        Map the feature dict (from feature_builder + market data) to the
        exact 59-column vector the LR model was trained on.

        The feature_builder produces GDELT-style signals. We map them to
        the notebook's column names, filling gaps with sensible defaults.
        """
        import numpy as np

        # Build a mapping from our runtime features → notebook feature names
        # feature_builder.py produces: gdelt_event_count, gdelt_min_goldstein,
        # gdelt_avg_tone, vix, market_stress_score, combined_avg_sentiment, etc.
        # We map these to the closest notebook equivalents.
        runtime_map = {
            # GDELT signals
            "total_events":          features.get("gdelt_event_count", 0) * 10,
            "total_articles":        features.get("gdelt_total_articles", 0),
            "conflict_events":       features.get("gdelt_event_count", 0),
            "coop_events":           max(0, features.get("gdelt_event_count", 0) * 3),
            "conflict_ratio":        min(features.get("gdelt_event_count", 0) / 20.0, 1.0),
            "goldstein_avg":         features.get("gdelt_min_goldstein", 0.0),
            "neg_goldstein_ratio":   min(abs(features.get("gdelt_min_goldstein", 0.0)) / 10.0, 1.0)
                                     if features.get("gdelt_min_goldstein", 0.0) < 0 else 0.0,
            "country_diversity":     10.0,  # not tracked at runtime
            # Sentiment → goldstein proxy
            "sentiment_score":       features.get("combined_avg_sentiment", 0.0),
            # Rolling features — use current value as proxy (no history at runtime)
            "total_events_roll7":    features.get("gdelt_event_count", 0) * 10,
            "total_events_roll14":   features.get("gdelt_event_count", 0) * 10,
            "conflict_ratio_roll7":  min(features.get("gdelt_event_count", 0) / 20.0, 1.0),
            "conflict_ratio_roll14": min(features.get("gdelt_event_count", 0) / 20.0, 1.0),
            "goldstein_avg_roll7":   features.get("gdelt_min_goldstein", 0.0),
            "goldstein_avg_roll14":  features.get("gdelt_min_goldstein", 0.0),
            "neg_goldstein_ratio_roll7":  min(abs(features.get("gdelt_min_goldstein", 0.0)) / 10.0, 1.0)
                                          if features.get("gdelt_min_goldstein", 0.0) < 0 else 0.0,
            "neg_goldstein_ratio_roll14": min(abs(features.get("gdelt_min_goldstein", 0.0)) / 10.0, 1.0)
                                          if features.get("gdelt_min_goldstein", 0.0) < 0 else 0.0,
            "conflict_events_roll7":  features.get("gdelt_event_count", 0),
            "conflict_events_roll14": features.get("gdelt_event_count", 0),
            # Lag features — use current value (no history at runtime)
            "conflict_ratio_lag1":   min(features.get("gdelt_event_count", 0) / 20.0, 1.0),
            "goldstein_lag1":        features.get("gdelt_min_goldstein", 0.0),
            "total_events_lag1":     features.get("gdelt_event_count", 0) * 10,
            "conflict_ratio_lag3":   min(features.get("gdelt_event_count", 0) / 20.0, 1.0),
            "goldstein_lag3":        features.get("gdelt_min_goldstein", 0.0),
            "total_events_lag3":     features.get("gdelt_event_count", 0) * 10,
            "conflict_ratio_lag7":   min(features.get("gdelt_event_count", 0) / 20.0, 1.0),
            "goldstein_lag7":        features.get("gdelt_min_goldstein", 0.0),
            "total_events_lag7":     features.get("gdelt_event_count", 0) * 10,
            "conflict_ratio_lag14":  min(features.get("gdelt_event_count", 0) / 20.0, 1.0),
            "goldstein_lag14":       features.get("gdelt_min_goldstein", 0.0),
            "total_events_lag14":    features.get("gdelt_event_count", 0) * 10,
            # Trend features — use 0 (no history at runtime)
            "conflict_trend":  0.0,
            "goldstein_trend": 0.0,
            "event_trend":     0.0,
            # Volatility — use 0 (no history at runtime)
            "goldstein_vol7":  0.0,
            # Stock market — map from market snapshot
            "VIX_close":   features.get("vix", 18.0),
            "VIX_ret":     0.0,
            "VIX_vol5":    0.05,
            "VIX_volume":  0.0,
            "SPY_ret":     features.get("sp500_change_pct", 0.0) / 100.0,
        }

        # Build vector: runtime_map overrides FEATURE_DEFAULTS
        vec = []
        for col in self.FEATURE_ORDER:
            if col in runtime_map:
                vec.append(float(runtime_map[col]))
            else:
                vec.append(float(self.FEATURE_DEFAULTS.get(col, 0.0)))

        return np.array(vec, dtype=np.float32).reshape(1, -1)

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_ready():
            logger.warning("PickleModelService not ready — falling back to DummyModelService")
            return DummyModelService().predict(features)

        try:
            import numpy as np

            feature_vector = self._build_feature_vector(features)

            # Apply scaler (required — model trained on scaled data)
            if self._scaler is not None:
                feature_vector = self._scaler.transform(feature_vector)
            else:
                logger.warning("PickleModelService: no scaler loaded — predictions may be inaccurate")

            # Predict: classes are [0=Low Risk, 1=High Risk]
            label = int(self._model.predict(feature_vector)[0])
            proba = self._model.predict_proba(feature_vector)[0]

            p_high = float(proba[1])   # P(High Risk)
            p_low  = float(proba[0])   # P(Low Risk)

            # Risk score: P(High Risk) * 100
            risk_score = round(p_high * 100.0, 2)

            return {
                "predicted_score": risk_score,
                "confidence": round(float(max(proba)), 3),
                "model_backend": "pickle",
                "components": {
                    "p_high_risk": round(p_high, 4),
                    "p_low_risk":  round(p_low, 4),
                    "label":       "High Risk" if label == 1 else "Low Risk",
                },
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
