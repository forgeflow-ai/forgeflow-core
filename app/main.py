from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.health import router as health_router


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

    app.include_router(health_router)
    return app


app = create_app()
