from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RINAVI_", env_file=".env")

    app_name: str = "RINAVI"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = f"sqlite+aiosqlite:///{_BACKEND_DIR.as_posix()}/rinavi.db"
    storage_dir: str = f"{_BACKEND_DIR.as_posix()}/data/vault"
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

    @model_validator(mode="after")
    def _reject_unsafe_production(self) -> "Settings":
        if self.environment in {"development", "test"}:
            return self
        if self.dev_signin_enabled:
            raise ValueError("dev sign-in must be disabled outside development")
        if not self.cookie_secure:
            raise ValueError("cookie_secure must be true outside development")
        if not self.webauthn_origin.startswith("https://"):
            raise ValueError("webauthn_origin must use https outside development")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
