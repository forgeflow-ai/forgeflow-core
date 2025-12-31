from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.db.session import get_db
from app.models.api_key import ApiKey
from app.models.user import User

router = APIRouter(tags=["auth"])
security = HTTPBearer(auto_error=False)


class UserResponse(BaseModel):
    """User response model."""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    created_at: str = Field(..., description="ISO 8601 timestamp in UTC")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "created_at": "2025-12-31T00:00:00Z"
            }
        }


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticate user via API key from Authorization header.
    Raises 401 if authentication fails.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )
    
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
    
    # Extract API key from Bearer token
    api_key = credentials.credentials
    
    # Find API key in database
    api_keys = db.query(ApiKey).all()
    matching_key: Optional[ApiKey] = None
    
    for key in api_keys:
        if verify_api_key(api_key, key.key_hash):
            # Check if key is expired
            if key.expires_at and key.expires_at < datetime.now(timezone.utc):
                continue
            
            matching_key = key
            # Update last_used_at
            key.last_used_at = datetime.now(timezone.utc)
            db.commit()
            break
    
    if matching_key is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key"
        )
    
    # Get user
    user = db.query(User).filter(User.id == matching_key.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Get current authenticated user information.
    
    Requires valid API key in Authorization header.
    Returns 401 if authentication fails.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at.isoformat() + "Z"
    )


@router.get("/admin/api-key")
def get_admin_api_key():
    """
    Get the seeded admin API key from file.
    
    This endpoint is only for initial setup. The API key is written to
    admin_api_key.txt during seed. This endpoint reads and returns it.
    """
    import os
    from pathlib import Path
    
    # Try to read from project root first
    key_file_path = Path("admin_api_key.txt")
    if not key_file_path.exists():
        # Try /tmp as fallback
        key_file_path = Path("/tmp/admin_api_key.txt")
    
    if not key_file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Admin API key file not found. Seed may not have run yet."
        )
    
    try:
        with open(key_file_path, "r") as f:
            content = f.read().strip()
            lines = content.split("\n")
            api_key = None
            email = None
            
            for line in lines:
                if line.startswith("API Key:"):
                    api_key = line.replace("API Key:", "").strip()
                elif line.startswith("Email:"):
                    email = line.replace("Email:", "").strip()
            
            if not api_key:
                raise HTTPException(
                    status_code=500,
                    detail="API key not found in file"
                )
            
            return {
                "email": email or "admin@forgeflow.local",
                "api_key": api_key,
                "message": "⚠️ IMPORTANT: Copy this API key. It will not be shown again after you use it!"
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading API key file: {str(e)}"
        )

