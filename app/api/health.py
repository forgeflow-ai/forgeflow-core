from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Application status", example="ok")
    timestamp: str = Field(..., description="ISO 8601 timestamp in UTC", example="2025-12-31T00:00:00Z")
    env: str = Field(..., description="Environment name", example="local")
    db_ok: bool = Field(..., description="Database connectivity status")
    db_error: Optional[str] = Field(None, description="Database error message if connection failed", example=None)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "timestamp": "2025-12-31T00:00:00Z",
                "env": "local",
                "db_ok": True,
                "db_error": None
            }
        }


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint. Returns application status and database connectivity.
    
    Returns:
        HealthResponse: Health status with database connectivity information
    """
    db_ok = False
    db_error: Optional[str] = None

    if db is None:
        db_error = "DATABASE_URL not set or database not configured"
    else:
        try:
            db.execute(text("SELECT 1"))
            db_ok = True
        except Exception as e:
            db_error = str(e)

    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat() + "Z",
        env=settings.ENV,
        db_ok=db_ok,
        db_error=db_error,
    )

