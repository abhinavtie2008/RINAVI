from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RINAVI_", env_file=".env")

    app_name: str = "RINAVI"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./rinavi.db"
    log_level: str = "INFO"

    cookie_name: str = "rinavi_session"
    cookie_secure: bool = False
    session_ttl_hours: int = 24 * 7
    dev_signin_enabled: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]
    consent_policy_version: str = "1.0"

    webauthn_rp_id: str = "localhost"
    webauthn_origin: str = "http://localhost:3000"
    webauthn_rp_name: str = "RINAVI"


@lru_cache
def get_settings() -> Settings:
    return Settings()
