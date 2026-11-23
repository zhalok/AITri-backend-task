from datetime import datetime, timezone
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/l10"
    # "now" is always read from here, never from the system clock.
    app_now: datetime = datetime(2026, 11, 11, 15, 0, 0, tzinfo=timezone.utc)
    company_timezone: str = "America/Chicago"


@lru_cache
def get_settings() -> Settings:
    return Settings()
