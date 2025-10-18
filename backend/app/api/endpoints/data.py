# backend/app/api/endpoints/data.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
import pandas as pd

from backend.app.database import get_db
# توحيد الموديلز على backend.app.models عشان نتجنب تعدد الـ Base
from backend.app.models import User, Log, DataSource  # لو عندك DataSource في models

router = APIRouter()


# --------- نماذج الإدخال من فريق الـ AI (اختياري) ----------
class AIRecord(BaseModel):
    uid: str
    type: str
    time: datetime
    params: dict
    isLocalIP: bool
    hour: int
    is_weekend: bool
    is_night: bool


class AIImport(BaseModel):
    records: List[AIRecord]


@router.post("/data/import-ai")
def import_ai_data(ai_import: AIImport, db: Session = Depends(get_db)):
    """
    استيراد بيانات فريق الـ AI. (مسار مساعد اختياري)
    """
    created = 0
    for r in ai_import.records:
        user = db.execute(
            select(User).where(User.uid == r.uid)
        ).scalar_one_or_none()
        if user is None:
            # لو المستخدم مش موجود نخلقه بشكل مبسط
            user = User(uid=r.uid, username=r.uid)
            db.add(user)
            db.flush()  # عشان ياخد id

        log = Log(
            user_id=user.id,
            activity_type=r.type,
            timestamp=r.time,
            params=r.params,
            hour=r.hour,
            is_weekend=r.is_weekend,
            is_night=r.is_night,
        )
        db.add(log)
        created += 1

    db.commit()
    return {"success": True, "inserted": created}
# ------------------------------------------------------------


@router.post("/data/upload-logs")
def upload_logs(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    رفع CSV لوجات ومعالجتها بسرعة وبشكل آمن.
    الأعمدة المطلوبة: username, timestamp, activity_type
    الاختيارية: source_ip, result
    """
    try:
        # نقرأ الملف في DataFrame
        df = pd.read_csv(file.file)

        # تحقق من الأعمدة
        required = ["username", "timestamp", "activity_type"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

        # تنظيف/تطبيع مبدئي
        df["username"] = df["username"].astype(str).str.strip()
        df["activity_type"] = df["activity_type"].astype(str).str.strip()

        # تحويل التوقيت؛ أي صف غير قابل للتحويل يُستبعد
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=False)
        before = len(df)
        df = df.dropna(subset=["timestamp", "username", "activity_type"])
        dropped = before - len(df)

        # اجمع usernames فريدة
        usernames = sorted(set(df["username"].tolist()))
        if not usernames:
            return {
                "upload_id": f"upload_{datetime.utcnow().timestamp()}",
                "processed_records": 0,
                "skipped_rows": dropped,
                "created_users": 0,
                "existing_users": 0,
                "processing_time": "n/a",
            }

        # هات المستخدمين الموجودين (id, username)
        existing_rows = db.execute(
            select(User.id, User.username).where(User.username.in_(usernames))
        ).all()

        # مهم: استخدم row.id و row.username بدل ['username'] لتفادي خطأ tuple indices
        user_map: Dict[str, int] = {row.username: row.id for row in existing_rows}
        existing_count = len(user_map)

        # أنشئ الناقصين
        missing_users = [u for u in usernames if u not in user_map]
        new_users: List[User] = []
        for uname in missing_users:
            # uid بسيط مشتق من الاسم
            new_users.append(User(username=uname, uid=f"uid_{uname}"))

        if new_users:
            db.bulk_save_objects(new_users)
            db.flush()
            # حدّث الخريطة بعد الإدراج
            new_rows = db.execute(
                select(User.id, User.username).where(User.username.in_(missing_users))
            ).all()
            for row in new_rows:
                user_map[row.username] = row.id

        created_users = len(missing_users)

        # بيلد اللوجز بالجملة مع تقطيع
        logs_to_insert: List[Log] = []
        processed = 0

        # أعمدة اختيارية
        has_src = "source_ip" in df.columns
        has_res = "result" in df.columns

        BATCH = 5000  # غيّرها حسب حجم جهازك

        for _, r in df.iterrows():
            uname = r["username"]
            uid = user_map.get(uname)
            if not uid:
                # لو لسه مش لاقيه لأي سبب نتخطى الصف
                continue

            logs_to_insert.append(
                Log(
                    user_id=uid,
                    timestamp=r["timestamp"].to_pydatetime()
                    if hasattr(r["timestamp"], "to_pydatetime")
                    else r["timestamp"],
                    activity_type=r["activity_type"],
                    source_ip=(r["source_ip"] if has_src else None),
                    result=(r["result"] if has_res else None),
                )
            )

            if len(logs_to_insert) >= BATCH:
                db.bulk_save_objects(logs_to_insert)
                db.flush()
                processed += len(logs_to_insert)
                logs_to_insert.clear()

        # ادفع الباقي
        if logs_to_insert:
            db.bulk_save_objects(logs_to_insert)
            db.flush()
            processed += len(logs_to_insert)

        db.commit()

        return {
            "upload_id": f"upload_{datetime.utcnow().timestamp()}",
            "processed_records": processed,
            "skipped_rows": dropped,
            "created_users": created_users,
            "existing_users": existing_count,
            "errors": 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        # أي خطأ غير متوقع
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")


@router.get("/data/sources")
def list_data_sources(db: Session = Depends(get_db)):
    """
    قائمة مصادر البيانات (لو الجدول موجود).
    """
    # لو DataSource مش موجود في سكيمتك، تقدر تشيل الـ import والـ endpoint ده
    sources = db.execute(select(DataSource)).scalars().all()

    return [
        {
            "id": s.id,
            "name": s.source_name,
            "type": s.source_type,
            "record_count": s.records_count,
            "last_sync": s.last_received.isoformat() if s.last_received else None,
            "status": s.status,
        }
        for s in sources
    ]
