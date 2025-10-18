from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, Dict, Any
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from pydantic import BaseModel

from backend.app.database import get_db
from backend.app.models import Alert, User, Log, AlertResolution

router = APIRouter()

# ======================
# 🔹 Helpers
# ======================

def _to_float(value: Any) -> Optional[float]:
    """Safely convert Decimal or None to float."""
    if isinstance(value, Decimal):
        return float(value)
    return value

def _date_to_dt_start(d: date) -> datetime:
    """Convert date to datetime (start of day)."""
    return datetime.combine(d, time.min)

def _date_to_dt_end(d: date) -> datetime:
    """Convert date to datetime (end of day)."""
    return datetime.combine(d, time.max)


# ======================
# 🔹 Endpoints
# ======================

@router.get("/alerts", summary="List alerts with filters and pagination")
def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    priority: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    type: Optional[str] = Query(None, alias="type"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Lists alerts with filtering, pagination, and joined user info.
    """
    q = db.query(Alert).options(joinedload(Alert.user))

    if priority:
        q = q.filter(Alert.priority == priority)
    if status:
        q = q.filter(Alert.alert_status == status)
    if user_id:
        q = q.filter(Alert.user_id == user_id)
    if type:
        q = q.filter(Alert.anomaly_type == type)
    if date_from:
        q = q.filter(Alert.detected_at >= _date_to_dt_start(date_from))
    if date_to:
        q = q.filter(Alert.detected_at <= _date_to_dt_end(date_to))

    total = q.count()

    alerts = (
        q.order_by(Alert.detected_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    alerts_list = [
        {
            "id": a.id,
            "user": {
                "id": a.user.id if a.user else None,
                "username": a.user.username if a.user else None,
                "department": a.user.department if a.user else None,
            },
            "anomaly_type": a.anomaly_type,
            "priority": a.priority,
            "confidence_score": _to_float(a.confidence_score),
            "risk_score": _to_float(a.risk_score),
            "risk_level": a.risk_level,
            "alert_status": a.alert_status,
            "explanation": a.explanation,
            "detailed_reasons": a.detailed_reasons,
            "geo_location": a.geo_location,
            "detected_at": a.detected_at.isoformat() if a.detected_at else None,
        }
        for a in alerts
    ]

    pri_counts = dict(db.query(Alert.priority, func.count(Alert.id)).group_by(Alert.priority).all())
    sta_counts = dict(db.query(Alert.alert_status, func.count(Alert.id)).group_by(Alert.alert_status).all())

    return {
        "alerts": alerts_list,
        "total": total,
        "filters": {
            "priorities": pri_counts,
            "statuses": sta_counts,
        },
        "pagination": {"skip": skip, "limit": limit},
    }


# ======================
# 🔹 Group by Priority (must come before /alerts/{id})
# ======================

@router.get("/alerts/by-priority", summary="Get grouped alerts by priority")
def get_alerts_by_priority(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Groups alerts by priority and returns the latest 10 per level.
    """
    levels = ["critical", "high", "medium", "low"]
    result: Dict[str, Any] = {}

    # Counts
    rows = db.query(Alert.priority, func.count(Alert.id)).group_by(Alert.priority).all()
    counts = {lvl: 0 for lvl in levels}
    for p, c in rows:
        counts[p or "unknown"] = c

    # Details
    for lvl in levels:
        last10 = (
            db.query(Alert)
            .options(joinedload(Alert.user))
            .filter(Alert.priority == lvl)
            .order_by(Alert.detected_at.desc())
            .limit(10)
            .all()
        )
        result[lvl] = {
            "count": counts.get(lvl, 0),
            "alerts": [
                {
                    "id": a.id,
                    "username": a.user.username if a.user else None,
                    "anomaly_type": a.anomaly_type,
                    "risk_score": _to_float(a.risk_score),
                    "detected_at": a.detected_at.isoformat() if a.detected_at else None,
                }
                for a in last10
            ],
        }

    return result


# ======================
# 🔹 Get Single Alert
# ======================

@router.get("/alerts/{alert_id}", summary="Get single alert details")
def get_alert_details(alert_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed view for a specific alert with recent log and placeholder timeline.
    """
    a = db.query(Alert).options(joinedload(Alert.user)).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")

    # آخر Log قبل وقت التنبيه
    log_details = None
    if a.user_id:
        log_details = (
            db.query(Log)
            .filter(Log.user_id == a.user_id, Log.timestamp <= a.detected_at)
            .order_by(Log.timestamp.desc())
            .first()
        )

    detection = {
        "ml_score": 0.89,
        "rule_score": 0.95,
        "final_risk": _to_float(a.risk_score),
        "confidence": _to_float(a.confidence_score),
    }

    timeline = []
    if a.detected_at:
        timeline = [
            {
                "timestamp": (a.detected_at - timedelta(minutes=10)).isoformat(),
                "event": "Login from Cairo, Egypt",
                "ip": "156.174.21.4",
            },
            {
                "timestamp": a.detected_at.isoformat(),
                "event": "Login from Paris, France",
                "ip": "45.62.11.8",
            },
        ]

    return {
        "alert": {
            "id": a.id,
            "user": {
                "id": a.user.id if a.user else None,
                "username": a.user.username if a.user else None,
            },
            "log_details": {
                "id": getattr(log_details, "id", None),
                "timestamp": getattr(log_details, "timestamp", None).isoformat()
                if getattr(log_details, "timestamp", None)
                else None,
                "activity_type": getattr(log_details, "activity_type", None),
                "source_ip": getattr(log_details, "source_ip", None),
                "params": getattr(log_details, "params", None),
            } if log_details else None,
            "detection_details": detection,
            "timeline": timeline,
        }
    }


# ======================
# 🔹 Update Status
# ======================

class AlertStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    assigned_to: Optional[str] = None


@router.put("/alerts/{alert_id}/status", summary="Update alert status")
def update_alert_status(alert_id: int, update: AlertStatusUpdate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Update alert status and append notes inline.
    """
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")

    allowed = {"new", "investigating", "resolved"}
    if update.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {sorted(allowed)}")

    a.alert_status = update.status

    if update.notes:
        note = f"[Note]: {update.notes}"
        a.explanation = f"{a.explanation}\n{note}" if a.explanation else note

    db.commit()
    db.refresh(a)
    return {"success": True, "message": f"Alert status updated to {a.alert_status}"}


# ======================
# 🔹 Resolve Alert
# ======================

class AlertResolutionUpdate(BaseModel):
    resolution: str
    notes: Optional[str] = None
    feedback: Optional[str] = None


@router.post("/alerts/{alert_id}/resolve", summary="Resolve an alert")
def resolve_alert(alert_id: int, body: AlertResolutionUpdate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Marks alert as resolved; upserts AlertResolution record.
    """
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")

    a.alert_status = "resolved"

    res = db.query(AlertResolution).filter(AlertResolution.alert_id == alert_id).first()
    now = datetime.utcnow()

    if res:
        res.resolution = body.resolution
        res.notes = body.notes
        res.feedback = body.feedback
        res.resolved_at = now
        res.resolved_by = "analyst_placeholder"
    else:
        res = AlertResolution(
            alert_id=alert_id,
            resolution=body.resolution,
            notes=body.notes,
            feedback=body.feedback,
            resolved_at=now,
            resolved_by="analyst_placeholder",
        )
        db.add(res)

    db.commit()
    return {"success": True, "message": "Alert has been resolved."}
