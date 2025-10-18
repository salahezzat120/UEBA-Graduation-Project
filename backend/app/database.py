# backend/app/database.py
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL

# جرّب أولاً DATABASE_URL النصّي (مثالي لـ Supabase)
DATABASE_URL = os.getenv("DATABASE_URL")

# بديل تجميعي لو مش متوفر DATABASE_URL
if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD")      # خام (بدون ترميز يدوي)
    DB_HOST = os.getenv("DB_HOST")              # مثال: db.xxxxx.supabase.co
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "postgres")

    if not (DB_PASSWORD and DB_HOST):
        raise RuntimeError("Set DATABASE_URL or DB_HOST/DB_PASSWORD env vars")

    DATABASE_URL = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER","postgres"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT","5432")),
        database=os.getenv("DB_NAME","postgres"),
        query={"sslmode": "require"},
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

# ⬇️ اللي محتاجاه endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
