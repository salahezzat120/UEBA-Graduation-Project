# backend/app/api/endpoints/dashboard.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text
from datetime import datetime, date, time, timedelta

from backend.app.database import get_db

# NOTE: لو الموديلز عندك في backend/models/models.py (وهو الصح حسب شجرتك)
try:
    from backend.app.models import User, Alert, DataSource
except Exception:
    # في بعض المشاريع القديمة كانت الموديلز تحت backend/app/models.py
    # fallback علشان ما يوقعش السيرفر لو المسار مختلف
    try:
        from backend.app.models import User, Alert, DataSource  # type: ignore
    except Exception:
        User = Alert = DataSource = None  # هنحمي الاستعلامات لاحقًا

router = APIRouter(tags=["System & Dashboard"])



@router.get("/system/status")
def system_status(db: Session = Depends(get_db)):
    """
    Health check: API + DB connectivity.
    """
    db_status = "disconnected"
    db_error = None
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_error = str(e)

    return {
        "status": "active",
        "version": "1.0.0",
        "uptime": "0h 0m",
        "database_status": db_status,
        "db_error": db_error,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/dashboard/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """
    KPIs for the main dashboard.
    آمنة ضد اختلاف أسماء الأعمدة/السكيمة.
    """
    # Defaults
    active_users = 0
    total_alerts = 0
    critical_alerts = 0
    resolved_today = 0
    accuracy_rate = 85.5  # Placeholder

    # Users
    try:
        if User is not None:
            q = db.query(func.count(User.id))
            if hasattr(User, "status"):
                q = q.filter(User.status == "active")
            active_users = q.scalar() or 0
    except Exception:
        active_users = 0

    # Alerts total
    try:
        if Alert is not None:
            total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    except Exception:
        total_alerts = 0

    # Critical alerts
    try:
        if Alert is not None and hasattr(Alert, "priority"):
            critical_alerts = db.query(func.count(Alert.id)).filter(Alert.priority == "critical").scalar() or 0
    except Exception:
        critical_alerts = 0

    # Resolved today
    try:
        if Alert is not None and hasattr(Alert, "alert_status") and hasattr(Alert, "detected_at"):
            today_start = datetime.combine(date.today(), time.min)
            resolved_today = (
                db.query(func.count(Alert.id))
                .filter(Alert.alert_status == "resolved", Alert.detected_at >= today_start)
                .scalar()
                or 0
            )
    except Exception:
        resolved_today = 0

    return {
        "system_status": "active",
        "last_update": datetime.utcnow().isoformat(),
        "metrics": {
            "active_users": active_users,
            "total_alerts": total_alerts,
            "critical_alerts": critical_alerts,
            "resolved_today": resolved_today,
            "accuracy_rate": accuracy_rate,
        },
    }


@router.get("/dashboard/high-risk-users")
def get_high_risk_users(limit: int = 10, db: Session = Depends(get_db)):
    """
    Top high-risk users (آمن ضد اختلاف السكيمة).
    """
    users_list = []
    total_count = 0

    try:
        if User is not None:
            query = db.query(User)
            if hasattr(User, "risk_score"):
                query = query.order_by(User.risk_score.desc())
            else:
                query = query.order_by(User.id.desc())

            high_risk_users = query.limit(limit).all()

            # Count where risk_score > 0.75 if exists
            if hasattr(User, "risk_score"):
                total_count = db.query(func.count(User.id)).filter(User.risk_score > 0.75).scalar() or 0
            else:
                total_count = db.query(func.count(User.id)).scalar() or 0

            for user in high_risk_users:
                users_list.append({
                    "id": getattr(user, "id", None),
                    "username": getattr(user, "username", None),
                    "uid": getattr(user, "uid", None),
                    "department": getattr(user, "department", None),
                    "risk_score": float(getattr(user, "risk_score", 0.0)) if getattr(user, "risk_score", None) is not None else None,
                    "anomaly_count": getattr(user, "anomaly_count", None),
                    "status": getattr(user, "status", None),
                })
    except Exception:
        # ارجع فاضي لو حصل أي خطأ
        users_list = []
        total_count = 0

    return {"users": users_list, "total": total_count}


@router.get("/dashboard/latest-alerts")
def get_latest_alerts(limit: int = 20, db: Session = Depends(get_db)):
    """
    Latest alerts (آمن ضد اختلاف السكيمة).
    """
    alerts_list = []
    total_alerts = 0

    try:
        if Alert is not None:
            query = db.query(Alert)
            # eager-load user relationship لو موجودة
            if hasattr(Alert, "user"):
                query = query.options(joinedload(Alert.user))
            if hasattr(Alert, "detected_at"):
                query = query.order_by(Alert.detected_at.desc())

            latest_alerts = query.limit(limit).all()
            total_alerts = db.query(func.count(Alert.id)).scalar() or 0

            for alert in latest_alerts:
                user_obj = getattr(alert, "user", None)
                alerts_list.append({
                    "id": getattr(alert, "id", None),
                    "username": getattr(user_obj, "username", None) if user_obj else None,
                    "anomaly_type": getattr(alert, "anomaly_type", None),
                    "priority": getattr(alert, "priority", None),
                    "risk_level": getattr(alert, "risk_level", None),
                    "risk_score": float(getattr(alert, "risk_score", 0.0)) if getattr(alert, "risk_score", None) is not None else None,
                    "alert_status": getattr(alert, "alert_status", None),
                    "explanation": getattr(alert, "explanation", None),
                    "detected_at": getattr(alert, "detected_at", None).isoformat() if getattr(alert, "detected_at", None) else None,
                    "geo_location": getattr(alert, "geo_location", None),
                })
    except Exception:
        alerts_list = []
        total_alerts = 0

    return {"alerts": alerts_list, "total": total_alerts}


@router.get("/dashboard/data-sources")
def get_data_sources_status(db: Session = Depends(get_db)):
    """
    Data sources status (آمن ضد اختلاف السكيمة).
    """
    sources_list = []
    try:
        if DataSource is not None:
            data_sources = db.query(DataSource).all()
            for source in data_sources:
                last_received = getattr(source, "last_received", None)
                sources_list.append({
                    "source_name": getattr(source, "source_name", None),
                    "source_type": getattr(source, "source_type", None),
                    "records_count": getattr(source, "records_count", None),
                    "last_received": last_received.isoformat() if last_received else None,
                    "status": getattr(source, "status", None),
                })
    except Exception:
        sources_list = []

    return {"sources": sources_list}


@router.get("/dashboard/resources")
def get_system_resources():
    """
    Mock system resource usage (Placeholder).
    """
    return {
        "cpu_usage": 45.2,
        "memory_usage": 62.8,
        "storage_usage": 78.5,
        "api_latency_avg": 120,  # ms
        "active_connections": 25,
    }


@router.get("/dashboard/trends")
def get_weekly_anomaly_trends(days: int = 7, db: Session = Depends(get_db)):
    """
    Weekly anomaly trend data (آمن ضد اختلاف السكيمة).
    """
    trends_list = []
    total_week = 0
    resolved_week = 0

    try:
        if Alert is not None and hasattr(Alert, "detected_at"):
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            trends_query = db.query(Alert).filter(Alert.detected_at.between(start_date, end_date)).all()
            trends_data = {}

            for alert in trends_query:
                detected_at = getattr(alert, "detected_at", None)
                if not detected_at:
                    continue
                date_str = detected_at.strftime("%Y-%m-%d")
                if date_str not in trends_data:
                    trends_data[date_str] = {"total_anomalies": 0, "resolved_anomalies": 0, "critical_count": 0}

                trends_data[date_str]["total_anomalies"] += 1
                if getattr(alert, "alert_status", None) == "resolved":
                    trends_data[date_str]["resolved_anomalies"] += 1
                if getattr(alert, "priority", None) == "critical":
                    trends_data[date_str]["critical_count"] += 1

            trends_list = [{"date": d, **vals} for d, vals in trends_data.items()]
            total_week = sum(d["total_anomalies"] for d in trends_data.values())
            resolved_week = sum(d["resolved_anomalies"] for d in trends_data.values())

    except Exception:
        trends_list = []
        total_week = 0
        resolved_week = 0

    return {
        "trends": sorted(trends_list, key=lambda x: x["date"]),
        "summary": {
            "total_week": total_week,
            "resolved_week": resolved_week,
            "trend": "decreasing",  # Placeholder
        },
    }
