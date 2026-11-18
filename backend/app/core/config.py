from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RINAVI_", env_file=".env")

    app_name: str = "RINAVI"
    environment: str = "production"
    api_v1_prefix: str = "/api/v1"
    database_url: str = f"sqlite+aiosqlite:///{_BACKEND_DIR.as_posix()}/rinavi.db"
    storage_dir: str = f"{_BACKEND_DIR.as_posix()}/data/vault"
    log_level: str = "INFO"

    cookie_name: str = "rinavi_session"
    cookie_secure: bool = False
    session_ttl_hours: int = 24 * 7
    # Dev sign-in is a sign-in bypass, so it is opt-in even in development:
    # a forgotten env file must not quietly enable it.
    dev_signin_enabled: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]
    consent_policy_version: str = "1.0"

    webauthn_rp_id: str = "localhost"
    webauthn_origin: str = "http://localhost:3000"
    webauthn_rp_name: str = "RINAVI"

    # slowapi/limits syntax. The global budget covers every request; the
    # per-route values are applied by the endpoint decorators.
    #
    # rate_limit_default is a per-IP ceiling, so it has to fit everybody who
    # shares one connection (a household, an office, a CSC counter).
    # rate_limit_session is the per-citizen budget: without a separate cap one
    # person's session could spend the whole IP allowance.
    rate_limit_default: str = "1200/hour"
    rate_limit_session: str = "200/hour"
    rate_limit_dev_signin: str = "5/minute"
    rate_limit_passkey_begin: str = "10/minute"
    rate_limit_passkey_finish: str = "20/minute"
    rate_limit_upload: str = "30/hour"
    rate_limit_document_content: str = "100/hour"
    rate_limit_export: str = "20/hour"
    # memory:// is per-process. Set a shared backend (for example
    # redis://localhost:6379/0 after installing the `redis` extra) when
    # running more than one worker or instance.
    rate_limit_storage_uri: str = "memory://"
    # Only enable behind a trusted reverse proxy that overwrites
    # X-Forwarded-For; otherwise clients can spoof their rate-limit key.
    trust_proxy_headers: bool = False

    @model_validator(mode="after")
    def _reject_unsafe_production(self) -> "Settings":
        # An omitted RINAVI_ENVIRONMENT falls back to "production", which then
        # trips one of the checks below. Those messages name a secondary
        # problem (for example "dev sign-in must be disabled outside
        # development") and send whoever is deploying to the wrong variable.
        # Name the actual cause first.
        if "environment" not in self.model_fields_set:
            raise ValueError(
                "RINAVI_ENVIRONMENT is not set. Set it explicitly to "
                "development, test or production; it no longer defaults to "
                "development."
            )
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
