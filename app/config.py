
"""Configuration centralisée de Pythonpédia."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Configuration de l'application."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Pythonpédia"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Serveur
    HOST: str = "127.0.0.1"
    PORT: int = Field(default=8888, ge=1, le=65535)

    # Stockage
    STORAGE_BACKEND: Literal["memory", "sqlite"] = "memory"
    DB_PATH: Path = BASE_DIR / "pythonpedia.db"

    # Réseau
    REQUEST_TIMEOUT: float = Field(default=5.0, gt=0, le=30)
    MAX_RESPONSE_BYTES: int = Field(
        default=1_048_576,
        gt=0,
    )
    MAX_CONCURRENT_REQUESTS: int = Field(
        default=10,
        ge=1,
        le=50,
    )

    # Administration
    ADMIN_API_KEY: SecretStr | None = None
    DISCOVERY_CANDIDATES: list[str] = []


@lru_cache
def get_settings() -> Settings:
    """Retourne la configuration partagée."""
    return Settings()
