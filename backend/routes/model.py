"""
routes/model.py
───────────────
POST /api/model/predict  — run risk prediction via the model service

Phase 1: DummyModelService (rule-based, always available)
Phase 2: PickleModelService (set MODEL_BACKEND=pickle in .env)

The feature vector is built from the database using the same
feature_builder used by the risk calculator — ensuring consistency.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from services.model_service import get_model_service
from scoring.feature_builder import build_features
from models.risk_score import RiskScore

router = APIRouter()


class PredictRequest(BaseModel):
    country_a: str
    country_b: str


@router.post("/model/predict")
def predict_risk(req: PredictRequest, db: Session = Depends(get_db)):
    """
    Predict risk score for a country pair using the configured model backend.

    Returns:
      - predicted_score: float (0–100)
      - confidence: float (0–1)
      - model_backend: str ("dummy" | "pickle")
      - components: dict of component scores
      - pair_key: str
      - predicted_at: ISO timestamp
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
        "pair_key": pair_key,
        "country_a": a,
        "country_b": b,
        "predicted_score": result["predicted_score"],
        "classification": RiskScore.classify(result["predicted_score"]),
        "confidence": result["confidence"],
        "model_backend": result["model_backend"],
        "components": result.get("components", {}),
        "predicted_at": datetime.utcnow().isoformat(),
        # TODO (Phase 2): Add feature importance / SHAP values here
    }


@router.get("/model/status")
def model_status():
    """Returns the current model backend status."""
    svc = get_model_service()
    from config import settings
    return {
        "backend": settings.model_backend,
        "is_ready": svc.is_ready(),
        "model_class": type(svc).__name__,
        "model_path": settings.model_path if settings.model_backend == "pickle" else None,
        # TODO (Phase 2): Add model version, training date, feature count
    }
