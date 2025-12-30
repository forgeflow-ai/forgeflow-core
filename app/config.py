import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ForgeFlow Core API"
    APP_VERSION: str = "0.0.1"

    ENV: str = os.getenv("ENV", "local")

    # Neon / Postgres
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")


settings = Settings()
