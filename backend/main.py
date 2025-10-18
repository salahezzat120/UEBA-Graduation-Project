import sys
import os
from fastapi import FastAPI

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import engine
from backend.app import models

# Create all database tables defined in models.models on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="UEBA Security Analytics Platform",
    description="Backend API for the User and Entity Behavior Analytics (UEBA) system.",
    version="1.0.0"
)

# Placeholder root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the UEBA Backend API"}

from app.api.endpoints import dashboard, users, alerts, analytics, detection, settings, data

app.include_router(dashboard.router, prefix="/api/v1", tags=["System & Dashboard"])
app.include_router(users.router, prefix="/api/v1", tags=["Users & Entities"])
app.include_router(alerts.router, prefix="/api/v1", tags=["Alerts & Anomalies"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics & Reports"])
app.include_router(detection.router, prefix="/api/v1", tags=["Detection & ML"])
app.include_router(settings.router, prefix="/api/v1", tags=["Settings & Configuration"])
app.include_router(data.router, prefix="/api/v1", tags=["Data Management"])

if __name__ == "__main__":
    import uvicorn
    # Use reload=True for development to automatically restart the server on code changes
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
