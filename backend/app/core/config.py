from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RINAVI_", env_file=".env")

    app_name: str = "RINAVI"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./rinavi.db"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
