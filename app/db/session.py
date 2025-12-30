from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

if not settings.DATABASE_URL:
    engine = None
    SessionLocal = None
else:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    if SessionLocal is None:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
