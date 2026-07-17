import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "AIEcosystem Backend"
    DEBUG: bool = True

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # PostgreSQL settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "ai_ecosystem"

    # Label Studio settings
    LABEL_STUDIO_URL: str = "http://localhost:8080"
    LABEL_STUDIO_API_KEY: str

    # Configure Pydantic to read from backend/.env
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate the settings for application-wide use
settings = Settings()
