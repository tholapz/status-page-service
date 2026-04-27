from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "status-page-service"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    port: int = 8000

    # NoDecode tells pydantic-settings to skip JSON-parsing for this field so
    # the field_validator below can handle plain comma-separated strings.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> object:
        if isinstance(v, str):
            stripped = v.strip()
            if stripped.startswith("["):
                import json
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return v

    database_url: str = "sqlite+aiosqlite:///./status.db"

    # Interval between automated service health checks (seconds).
    check_interval_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
