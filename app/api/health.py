from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """
    Health check endpoint. Returns application status and database connectivity.
    """
    db_ok = False
    db_error = None

    if db is None:
        db_error = "DATABASE_URL not set or database not configured"
    else:
        try:
            db.execute(text("SELECT 1"))
            db_ok = True
        except Exception as e:
            db_error = str(e)

    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "env": settings.ENV,
        "db_ok": db_ok,
        "db_error": db_error,
    }

