# UEBA Security Analytics Platform - Backend

This directory contains the backend for the UEBA Security Analytics Platform, a powerful API built with FastAPI and SQLAlchemy.

## 1. Overview

The backend provides a comprehensive API for user and entity behavior analytics, including data ingestion, anomaly detection, user risk scoring, and alert management. It is designed to integrate with a frontend dashboard and an AI processing pipeline.

### Key Technologies
- **Framework:** FastAPI
- **Database:** SQLAlchemy ORM (compatible with PostgreSQL and SQLite)
- **Data Validation:** Pydantic
- **Server:** Uvicorn

---

## 2. Setup and Installation

### Prerequisites
- Python 3.8+
- A virtual environment manager (e.g., `venv`)

### Installation Steps

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r ../requirements.txt
    ```

4.  **Configure the Database:**
    - The application uses a `.env` file to manage the database connection string.
    - Create a file named `.env` in the root directory (`UEBA-Graduation-Project`).
    - Add the `DATABASE_URL` variable to this file.

    **For SQLite (default for testing):**
    ```
    DATABASE_URL="sqlite:///./ueba_test.db"
    ```

    **For PostgreSQL (recommended for production):**
    ```
    DATABASE_URL="postgresql://user:password@localhost/ueba_db"
    ```

---

## 3. Running the Application

Once the setup is complete, you can run the application using Uvicorn.

From the `UEBA-Graduation-Project` root directory, run:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --app-dir backend --reload
```
- `--reload`: Enables auto-reloading when code changes are detected (useful for development).

The API will be available at `http://localhost:8080`.

---

## 4. API Documentation

The API includes automatically generated, interactive documentation. Once the server is running, you can access it at:

- **Swagger UI:** [http://localhost:8080/docs](http://localhost:8080/docs)
- **ReDoc:** [http://localhost:8080/redoc](http://localhost:8080/redoc)

---

## 5. Project Structure

- `app/`: Main application directory.
  - `api/`: Contains all the API endpoint routers, organized by category.
  - `database.py`: Handles database connection and session management.
  - `main.py`: The main FastAPI application entry point.
- `models/`: Contains all SQLAlchemy database models.
- `data/`: Includes sample data files for testing and development.
