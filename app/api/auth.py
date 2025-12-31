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

