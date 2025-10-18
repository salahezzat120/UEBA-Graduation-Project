# UEBA Security Analytics Platform - API Contract

## 1. Overview
This document provides the official API contract for the UEBA Security Analytics Platform backend. It includes details on authentication, response formats, and a complete specification of all available endpoints.

- **Version:** 1.0.0
- **Base URL:** `/api/v1`
- **Contact:** Backend Team

---

## 2. Authentication
All API requests must be authenticated using a **Bearer Token (JWT)**. The token should be included in the `Authorization` header of every request.

**Example Header:**
```
Authorization: Bearer <your_jwt_token>
```

---

## 3. Standard Response Format
All API responses follow a standardized JSON format.

**Success Response (`200 OK`):**
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "timestamp": "2025-10-17T10:30:00Z"
}
```

**Error Response (e.g., `400 Bad Request`, `404 Not Found`):**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "A description of the error",
    "details": { ... }
  },
  "timestamp": "2025-10-17T10:30:00Z"
}
```

---

## 4. API Endpoints

### Category 1: System & Dashboard (7 Endpoints)
- **`GET /api/v1/system/status`**: System health and status.
- **`GET /api/v1/dashboard/metrics`**: Dashboard KPIs and performance metrics.
- **`GET /api/v1/dashboard/high-risk-users`**: Top high-risk users for the dashboard.
- **`GET /api/v1/dashboard/latest-alerts`**: Recent alerts for the dashboard.
- **`GET /api/v1/dashboard/data-sources`**: Data source status and statistics.
- **`GET /api/v1/dashboard/resources`**: System resources usage.
- **`GET /api/v1/dashboard/trends`**: Weekly anomaly trends.

### Category 2: Users & Entities (5 Endpoints)
- **`GET /api/v1/users`**: List all users with filtering and pagination.
- **`GET /api/v1/users/{user_id}`**: User detailed profile with anomaly history.
- **`PUT /api/v1/users/{user_id}/status`**: Update user status (lock, suspend, activate).
- **`GET /api/v1/users/{user_id}/history`**: User anomaly history with a timeline.
- **`GET /api/v1/users/{user_id}/analytics`**: User behavior analytics.

### Category 3: Alerts & Anomalies (5 Endpoints)
- **`GET /api/v1/alerts`**: List alerts with filtering and pagination.
- **`GET /api/v1/alerts/{alert_id}`**: Alert detailed view with full context.
- **`PUT /api/v1/alerts/{alert_id}/status`**: Update alert status and add notes.
- **`GET /api/v1/alerts/by-priority`**: Group alerts by priority level.
- **`POST /api/v1/alerts/{alert_id}/resolve`**: Mark an alert as resolved with resolution details.

### Category 4: Analytics & Reports (4 Endpoints)
- **`GET /api/v1/analytics/trends`**: Time-based trends and patterns.
- **`GET /api/v1/analytics/risk-distribution`**: Risk distribution by department, user type, etc.
- **`GET /api/v1/analytics/export`**: Export analytics report in various formats.
- **`GET /api/v1/analytics/department-stats`**: Department-wise statistics and comparisons.

### Category 5: Detection & ML (4 Endpoints)
- **`POST /api/v1/detection/run`**: Run anomaly detection on recent data.
- **`GET /api/v1/detection/status`**: Detection engine status and health.
- **`POST /api/v1/detection/retrain`**: Trigger model retraining with new data.
- **`GET /api/v1/ml/model-info`**: Current ML model information and performance.

### Category 6: Settings & Configuration (6 Endpoints)
- **`GET /api/v1/settings/{category}`**: Get settings by category.
- **`PUT /api/v1/settings/{category}`**: Update settings configuration.
- **`GET /api/v1/notifications/channels`**: List notification channels.
- **`POST /api/v1/notifications/test`**: Test a notification channel.
- **`GET /api/v1/access-control/roles`**: List user roles and permissions.
- **`PUT /api/v1/access-control/roles/{role_id}`**: Update role permissions.

### Category 7: Data Management (4 Endpoints)
- **`POST /api/v1/data/import-ai`**: Import AI team processed data.
- **`POST /api/v1/data/upload-logs`**: Upload CSV log files.
- **`GET /api/v1/data/sources`**: List and manage data sources.
- **`GET /api/v1/data/quality`**: Data quality metrics and validation.

---

## 5. Further Documentation
For detailed information on request parameters, response bodies, and schemas for each endpoint, please refer to the interactive OpenAPI (Swagger) documentation available at the `/docs` endpoint of the running application.
