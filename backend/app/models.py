# backend/app/models.py
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint,
    Index, Numeric
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.types import JSON

# لو شغّال على PostgreSQL هنستخدم JSONB (أسرع في الفهرسة/الاستعلام)
try:
    from sqlalchemy.dialects.postgresql import JSONB as JSON_TYPE
except Exception:
    JSON_TYPE = JSON

Base = declarative_base()

# =====================================
# 1) Users
# =====================================
class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True)
    uid         = Column(String(100), nullable=False, unique=True, index=True)
    username    = Column(String(50),  nullable=False, unique=True, index=True)
    email       = Column(String(100), unique=True, index=True)
    department  = Column(String(50),  index=True)
    role        = Column(String(50))
    status      = Column(String(20),  default="active", index=True)   # active, locked, suspended
    risk_score  = Column(Numeric(5, 4), default=0.0, index=True)
    anomaly_count = Column(Integer, default=0)
    created_at  = Column(DateTime, default=datetime.utcnow, index=True)

    # علاقات
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    logs   = relationship("Log",   back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("uid", name="uq_users_uid"),
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_department_status", "department", "status"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} status={self.status}>"


# =====================================
# 2) Logs (User Activity)
# =====================================
class Log(Base):
    __tablename__ = "logs"

    id            = Column(Integer, primary_key=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type = Column(String(50), index=True)
    timestamp     = Column(DateTime, nullable=False, index=True)
    source_ip     = Column(String(45))
    result        = Column(String(20))

    # AI / سياق إضافي
    params        = Column(JSON_TYPE)      # لو PG → JSONB
    hour          = Column(Integer)
    is_weekend    = Column(Boolean)
    is_night      = Column(Boolean)

    user = relationship("User", back_populates="logs")

    __table_args__ = (
        Index("ix_logs_user_ts", "user_id", "timestamp"),
        Index("ix_logs_activity_ts", "activity_type", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Log id={self.id} user_id={self.user_id} type={self.activity_type!r}>"


# =====================================
# 3) Alerts (Anomalies)
# =====================================
class Alert(Base):
    __tablename__ = "alerts"

    id               = Column(Integer, primary_key=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    anomaly_type     = Column(String(50), index=True)
    priority         = Column(String(20), index=True)  # critical, high, medium, low
    risk_score       = Column(Numeric(5, 4))
    risk_level       = Column(String(20))
    confidence_score = Column(Numeric(5, 4))
    alert_status     = Column(String(20), default="new", index=True)  # new, investigating, resolved
    explanation      = Column(Text)
    detailed_reasons = Column(JSON_TYPE)
    geo_location     = Column(JSON_TYPE)
    detected_at      = Column(DateTime, default=datetime.utcnow, index=True)

    user        = relationship("User", back_populates="alerts")
    resolution  = relationship("AlertResolution", back_populates="alert", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_alerts_user_detected", "user_id", "detected_at"),
        Index("ix_alerts_status_priority", "alert_status", "priority"),
    )

    def __repr__(self) -> str:
        return f"<Alert id={self.id} user_id={self.user_id} type={self.anomaly_type!r} status={self.alert_status}>"


# =====================================
# 4) Alert Resolution
# =====================================
class AlertResolution(Base):
    __tablename__ = "alert_resolutions"

    id          = Column(Integer, primary_key=True)
    alert_id    = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    resolution  = Column(String(50))     # false_positive, verified_threat, ...
    notes       = Column(Text)
    feedback    = Column(String(100))
    resolved_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_by = Column(String(100))    # analyst id / user id

    alert = relationship("Alert", back_populates="resolution")


# =====================================
# 5) Data Sources
# =====================================
class DataSource(Base):
    __tablename__ = "data_sources"

    id            = Column(Integer, primary_key=True)
    source_name   = Column(String(100), nullable=False, index=True)
    source_type   = Column(String(50),  nullable=False, unique=True, index=True)
    records_count = Column(Integer, default=0)
    last_received = Column(DateTime, index=True)
    status        = Column(String(20), default="inactive", index=True)  # active, inactive, error

    __table_args__ = (
        Index("ix_data_sources_status_last", "status", "last_received"),
    )


# =====================================
# 6) Settings
# =====================================
class Setting(Base):
    __tablename__ = "settings"

    id          = Column(Integer, primary_key=True)
    category    = Column(String(50), nullable=False, index=True)
    key         = Column(String(100), nullable=False, unique=True, index=True)
    value       = Column(String(255))
    description = Column(Text)


# =====================================
# 7) Notification Channels
# =====================================
class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id            = Column(Integer, primary_key=True)
    channel_type  = Column(String(20),  nullable=False, index=True)  # email, webhook, slack
    channel_name  = Column(String(100), nullable=False, index=True)
    configuration = Column(JSON_TYPE, nullable=False)
    alert_levels  = Column(JSON_TYPE)   # ["critical", "high", ...]
    is_active     = Column(Boolean, default=True, index=True)

    __table_args__ = (
        Index("ix_notification_channels_active_type", "is_active", "channel_type"),
    )


# =====================================
# 8) Access Control Roles
# =====================================
class Role(Base):
    __tablename__ = "roles"

    id          = Column(Integer, primary_key=True)
    role_name   = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    permissions = Column(JSON_TYPE)  # {"view_alerts": true, "manage_users": false}


# =====================================
# 9) Detection Jobs
# =====================================
class DetectionJob(Base):
    __tablename__ = "detection_jobs"

    id               = Column(String(100), primary_key=True)  # detection_id
    status           = Column(String(20), default="running", index=True)  # running, completed, failed
    processed_logs   = Column(Integer)
    anomalies_found  = Column(Integer)
    high_risk_count  = Column(Integer)
    execution_time   = Column(String(20))
    created_at       = Column(DateTime, default=datetime.utcnow, index=True)


# =====================================
# 10) ML Models
# =====================================
class MLModel(Base):
    __tablename__ = "ml_models"

    id                  = Column(Integer, primary_key=True)
    name                = Column(String(100), index=True)
    version             = Column(String(20), unique=True, index=True)
    trained_at          = Column(DateTime, index=True)
    training_data_size  = Column(Integer)
    features            = Column(Integer)
    accuracy            = Column(Numeric(5, 4))
    false_positive_rate = Column(Numeric(5, 4))
    detection_latency   = Column(String(20))
    is_active           = Column(Boolean, default=False, index=True)

    __table_args__ = (
        Index("ix_ml_models_active_version", "is_active", "version"),
    )


# =====================================
# 11) System Metrics (تاريخ/مؤشرات)
# =====================================
class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id               = Column(Integer, primary_key=True)
    timestamp        = Column(DateTime, default=datetime.utcnow, index=True)
    cpu_usage        = Column(Numeric(5, 2))
    memory_usage     = Column(Numeric(5, 2))
    storage_usage    = Column(Numeric(5, 2))
    api_latency_avg  = Column(Integer)
    active_connections = Column(Integer)
