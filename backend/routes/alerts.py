"""routes/alerts.py — GET /api/alerts, PATCH /api/alerts/{id}/read"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db
from models.alert import Alert

router = APIRouter()


@router.get("/alerts")
def get_alerts(unread_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(Alert).filter(
        Alert.triggered_at >= datetime.utcnow() - timedelta(hours=48)
    )
    if unread_only:
        query = query.filter(Alert.is_read == False)  # noqa: E712
    alerts = query.order_by(Alert.triggered_at.desc()).limit(50).all()
    return {
        "alerts": [
            {
                "id": a.id,
                "pair_key": a.pair_key,
                "country_a": a.country_a,
                "country_b": a.country_b,
                "alert_type": a.alert_type,
                "title": a.title,
                "message": a.message,
                "severity": a.severity,
                "prev_score": a.prev_score,
                "new_score": a.new_score,
                "score_delta": a.score_delta,
                "is_read": a.is_read,
                "triggered_at": a.triggered_at.isoformat(),
            }
            for a in alerts
        ],
        "unread_count": db.query(Alert).filter(Alert.is_read == False).count(),  # noqa: E712
    }


@router.patch("/alerts/{alert_id}/read")
def mark_read(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter_by(id=alert_id).first()
    if alert:
        alert.is_read = True
        db.commit()
    return {"ok": True}


@router.patch("/alerts/read-all")
def mark_all_read(db: Session = Depends(get_db)):
    db.query(Alert).filter(Alert.is_read == False).update({"is_read": True})  # noqa: E712
    db.commit()
    return {"ok": True}

