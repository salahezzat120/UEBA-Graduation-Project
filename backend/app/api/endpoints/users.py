from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from ...models import User, Alert, Log
from typing import Optional
from fastapi import HTTPException
from pydantic import BaseModel

router = APIRouter()

@router.get("/users")
def get_users(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    department: Optional[str] = None,
    risk_min: Optional[float] = Query(None, ge=0, le=1),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lists all users with filtering and pagination.
    """
    query = db.query(User)
    
    if status:
        query = query.filter(User.status == status)
    if department:
        query = query.filter(User.department == department)
    if risk_min is not None:
        query = query.filter(User.risk_score >= risk_min)
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
        
    total_users = query.with_entities(func.count(User.id)).scalar()
    users = query.order_by(User.id).offset(skip).limit(limit).all()
    
    users_list = [
        {
            "id": user.id,
            "username": user.username,
            "uid": user.uid,
            "email": user.email,
            "department": user.department,
            "role": user.role,
            "status": user.status,
            "risk_score": float(user.risk_score),
            "anomaly_count": user.anomaly_count,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]
    
    return {
        "users": users_list,
        "total": total_users,
        "page": (skip // limit) + 1,
        "pages": (total_users + limit - 1) // limit
    }

@router.get("/users/{user_id}")
def get_user_details(user_id: int, db: Session = Depends(get_db)):
    """
    Provides a detailed profile for a specific user, including anomaly history.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    anomalies = db.query(Alert).filter(Alert.user_id == user_id).order_by(Alert.detected_at.desc()).limit(10).all()
    recent_activity = db.query(Log).filter(Log.user_id == user_id).order_by(Log.timestamp.desc()).limit(10).all()
    
    user_details = {
        "id": user.id,
        "username": user.username,
        "uid": user.uid,
        "email": user.email,
        "department": user.department,
        "status": user.status,
        "risk_score": float(user.risk_score),
        "created_at": user.created_at.isoformat()
    }
    
    anomalies_list = [
        {
            "id": anomaly.id,
            "anomaly_type": anomaly.anomaly_type,
            "priority": anomaly.priority,
            "risk_score": float(anomaly.risk_score),
            "explanation": anomaly.explanation,
            "detected_at": anomaly.detected_at.isoformat(),
            "alert_status": anomaly.alert_status
        }
        for anomaly in anomalies
    ]
    
    activity_list = [
        {
            "id": activity.id,
            "activity_type": activity.activity_type,
            "timestamp": activity.timestamp.isoformat(),
            "source_ip": activity.source_ip,
            "result": activity.result,
            "hour": activity.hour,
            "is_weekend": activity.is_weekend,
            "is_night": activity.is_night
        }
        for activity in recent_activity
    ]
    
    return {
        "user": user_details,
        "anomalies": anomalies_list,
        "recent_activity": activity_list
    }

class UserStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None

@router.put("/users/{user_id}/status")
def update_user_status(user_id: int, status_update: UserStatusUpdate, db: Session = Depends(get_db)):
    """
    Updates a user's status (e.g., lock, suspend, activate).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if status_update.status not in ["active", "locked", "suspended"]:
        raise HTTPException(status_code=400, detail="Invalid status value")
        
    user.status = status_update.status
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "message": f"User status updated to {user.status}",
        "user": {
            "id": user.id,
            "username": user.username,
            "status": user.status
        }
    }

@router.get("/users/{user_id}/history")
def get_user_anomaly_history(
    user_id: int,
    days: int = 30,
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Provides a timeline of a user's anomaly history.
    """
    import datetime

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)
    
    query = db.query(Alert).filter(
        Alert.user_id == user_id,
        Alert.detected_at.between(start_date, end_date)
    )
    
    if type:
        query = query.filter(Alert.anomaly_type == type)
        
    anomalies = query.order_by(Alert.detected_at.desc()).all()
    
    history_data = {}
    for anomaly in anomalies:
        date_str = anomaly.detected_at.strftime("%Y-%m-%d")
        if date_str not in history_data:
            history_data[date_str] = {"anomalies": []}
        
        history_data[date_str]["anomalies"].append({
            "id": anomaly.id,
            "type": anomaly.anomaly_type,
            "risk_score": float(anomaly.risk_score),
            "status": anomaly.alert_status
        })
        
    history_list = [
        {"date": date, **data} for date, data in history_data.items()
    ]
    
    total_anomalies = len(anomalies)
    resolved = sum(1 for a in anomalies if a.alert_status == "resolved")
    
    return {
        "history": sorted(history_list, key=lambda x: x["date"], reverse=True),
        "summary": {
            "total_anomalies": total_anomalies,
            "resolved": resolved,
            "pending": total_anomalies - resolved
        }
    }

@router.get("/users/{user_id}/analytics")
def get_user_behavior_analytics(user_id: int, db: Session = Depends(get_db)):
    """
    Provides behavior analytics for a specific user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # In a real-world scenario, this data would be pre-calculated and stored,
    # likely by a separate analytics or machine learning pipeline.
    # Using placeholder data for this implementation.
    
    behavior_pattern = {
        "typical_hours": [8, 9, 10, 11, 14, 15, 16, 17],
        "common_locations": ["Egypt", "UAE"],
        "frequent_activities": ["login", "file_access"],
        "risk_trend": "stable"
    }
    
    statistics = {
        "avg_daily_logins": 4.2,
        "weekend_activity": 15, # percentage
        "night_activity": 5 # percentage
    }
    
    return {
        "behavior_pattern": behavior_pattern,
        "statistics": statistics
    }





