import sys
import secrets
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import settings and routers from app package
from app.core.config import settings
from app.core.security import hash_api_key
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.flows import router as flows_router
from app.db.session import get_session_local
from app.models.user import User
from app.models.api_key import ApiKey

logger = logging.getLogger(__name__)


def seed_admin_user():
    """Seed admin user and API key if database is empty."""
    SessionLocal = get_session_local()
    if SessionLocal is None:
        logger.warning("Database not configured, skipping admin user seed")
        return
    
    db = SessionLocal()
    try:
        # Check if any user exists
        user_count = db.query(User).count()
        
        if user_count > 0:
            logger.info("Users already exist, skipping admin user seed")
            return
        
        # Create admin user
        admin_user = User(
            email="admin@forgeflow.local",
            password_hash="dummy_hash_for_seeded_user"  # Not used for API key auth
        )
        db.add(admin_user)
        db.flush()  # Get the user ID
        
        # Generate API key
        api_key_plain = f"ff_{secrets.token_urlsafe(32)}"
        api_key_hash = hash_api_key(api_key_plain)
        
        # Create API key
        api_key = ApiKey(
            user_id=admin_user.id,
            key_hash=api_key_hash,
            name="Admin API Key (Seeded)"
        )
        db.add(api_key)
        db.commit()
        
        # Log the plaintext key
        logger.info("=" * 80)
        logger.info("ADMIN USER SEEDED")
        logger.info("=" * 80)
        logger.info(f"Email: admin@forgeflow.local")
        logger.info(f"API Key: {api_key_plain}")
        logger.info("=" * 80)
        logger.info("⚠️  IMPORTANT: Copy this API key from the logs. It will not be shown again!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error seeding admin user: {e}")
        db.rollback()
    finally:
        db.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    origins = ["*"] if settings.CORS_ORIGINS == "*" else [o.strip() for o in settings.CORS_ORIGINS.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(flows_router)
    
    # Seed admin user on startup
    @app.on_event("startup")
    async def startup_event():
        seed_admin_user()

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

