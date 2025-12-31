from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional

from app.core.config import settings

# Lazy initialization - only create engine when needed
_engine: Optional[object] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        if settings.DATABASE_URL and settings.DATABASE_URL.strip():
            _engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_session_local():
    """Get or create the session maker."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        if engine is not None:
            _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def get_db():
    """Dependency for getting database session."""
    SessionLocal = get_session_local()
    if SessionLocal is None:
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
