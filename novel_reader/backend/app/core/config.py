from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> app/core -> app -> backend -> novel_reader/
NOVEL_READER_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(NOVEL_READER_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Inkwell Novel Reader"
    environment: Literal["local", "production"] = "local"

    database_url_test: str = ""
    database_url_production: str = ""
    secret_key: str = ""

    # Names must match .env.example (ACCESS_TOKEN_TTL_MINUTES / REFRESH_TOKEN_TTL_DAYS).
    access_token_ttl_minutes: int = Field(default=20, ge=1, le=1440)
    refresh_token_ttl_days: int = Field(default=14, ge=1, le=365)

    admin_username: str = "admin"
    admin_password: str = "change-me"

    novel_root: Path = Path("../drafts/Novel")
    cors_origins: str = "http://localhost:5173"

    @field_validator("database_url_test", "database_url_production", mode="before")
    @classmethod
    def normalize_postgres_driver(cls, value: object) -> str:
        """Provider links are often plain postgresql:// (psycopg2); the app is async."""
        url = str(value)
        for prefix in ("postgresql+psycopg2://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+asyncpg://" + url[len(prefix):]
        return url

    @field_validator("novel_root", mode="before")
    @classmethod
    def resolve_novel_root(cls, value: object) -> Path:
        path = Path(str(value))
        return path if path.is_absolute() else (NOVEL_READER_ROOT / path).resolve()

    @property
    def database_url(self) -> str:
        """Active URL. Production is selected only when explicitly configured."""
        return self.database_url_test if self.environment == "local" else self.database_url_production

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_required(self) -> None:
        # Messages intentionally never include the values themselves.
        missing = [name for name, value in (
            ("SECRET_KEY", self.secret_key),
            ("DATABASE_URL_TEST", self.database_url_test),
        ) if not value]
        if missing:
            raise RuntimeError(f"Missing required settings: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
