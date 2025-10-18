from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from ...models import Alert, User
import datetime

router = APIRouter()

@router.get("/analytics/trends")
def get_analytics_trends(
    period: str = "day",
    metric: str = "anomalies",
    db: Session = Depends(get_db)
):
    """
    Provides time-based trends and patterns for key metrics.
    """
    # This is a simplified implementation. A real-world application would
    # use a more robust time-series database or pre-aggregated data.
    
    end_date = datetime.date.today()
    if period == "week":
        start_date = end_date - datetime.timedelta(weeks=1)
    elif period == "month":
        start_date = end_date - datetime.timedelta(days=30)
    else:
        start_date = end_date - datetime.timedelta(days=1)
        
    if metric == "anomalies":
        query = db.query(Alert).filter(Alert.detected_at.between(start_date, end_date))
    elif metric == "users":
        query = db.query(User).filter(User.created_at.between(start_date, end_date))
    else: # risk_scores
        query = db.query(Alert).filter(Alert.detected_at.between(start_date, end_date))

    # Dummy data for demonstration
    trends_data = [
        {
            "date": "2025-10-17",
            "total_anomalies": 12,
            "high_risk_users": 5,
            "avg_risk_score": 0.35
        }
    ]
    
    return {
        "trends": trends_data,
        "comparison": {
            "vs_previous_period": "+15%",
            "trend_direction": "increasing"
        }
    }

@router.get("/analytics/risk-distribution")
def get_risk_distribution(
    group_by: str = "department",
    db: Session = Depends(get_db)
):
    """
    Provides risk distribution by department, user type, or time.
    """
    # This is a simplified implementation. A real-world application would
    # use more complex aggregation queries.
    
    if group_by == "department":
        query = db.query(User.department, User.risk_score).all()
    elif group_by == "user_type":
        query = db.query(User.role, User.risk_score).all()
    else: # hour, day_of_week
        query = db.query(Alert.detected_at, Alert.risk_score).all()

    # Dummy data for demonstration
    distribution_data = [
        {
            "department": "IT",
            "high_risk_users": 8,
            "total_users": 45,
            "risk_percentage": 17.8
        },
        {
            "department": "Finance",
            "high_risk_users": 12,
            "total_users": 32,
            "risk_percentage": 37.5
        }
    ]
    
    return {"distribution": distribution_data}

@router.get("/analytics/export")
def export_analytics_report(
    format: str = "pdf",
    period: str = "week",
    sections: str = "all"
):
    """
    Exports an analytics report in various formats.
    """
    # In a real-world application, this would trigger a background job
    # to generate the report and provide a URL to download it.
    
    # Placeholder implementation
    export_url = f"https://api.ueba-system.com/exports/report_20251017.{format}"
    expires_at = (datetime.datetime.utcnow() + datetime.timedelta(hours=24)).isoformat()
    
    return {
        "export_url": export_url,
        "expires_at": expires_at,
        "file_size": "2.5MB"
    }

@router.get("/analytics/department-stats")
def get_department_stats(db: Session = Depends(get_db)):
    """
    Provides department-wise statistics and comparisons.
    """
    # This is a simplified implementation. A real-world application would
    # use more complex aggregation queries and pre-calculated data.
    
    departments_data = [
        {
            "name": "IT",
            "users": 45,
            "anomalies": 28,
            "risk_score_avg": 0.42,
            "top_threats": ["after_hours", "privilege_escalation"]
        }
    ]
    
    insights = [
        "IT department shows 25% higher risk than average",
        "Finance has most impossible travel incidents"
    ]
    
    return {
        "departments": departments_data,
        "insights": insights
    }





