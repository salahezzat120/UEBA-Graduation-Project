# backend/app/main.py
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

from fastapi import FastAPI
from backend.app.database import engine
from . import models  # الموديلز الرسمية (backend/models/models.py)

from backend.app.api.endpoints import (
    dashboard, users, alerts, analytics, detection, settings, data
)

app = FastAPI(
    title="UEBA Security Analytics Platform API",
    description="API for the User and Entity Behavior Analytics (UEBA) system.",
    version="1.0.0",
)

# أنشئ الجداول عند الإقلاع (لو ماعندكش Alembic)
@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=engine)

# اضافة الراوترز
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(users.router,     prefix="/api/v1")
app.include_router(alerts.router,    prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(detection.router, prefix="/api/v1")
app.include_router(settings.router,  prefix="/api/v1")
app.include_router(data.router,      prefix="/api/v1")


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the UEBA Security Analytics Platform API"}
