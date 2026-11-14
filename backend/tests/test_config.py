import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings

_SAFE_PRODUCTION = {
    "environment": "production",
    "dev_signin_enabled": False,
    "cookie_secure": True,
    "webauthn_origin": "https://rinavi.example",
}


def test_safe_production_settings_are_accepted() -> None:
    settings = Settings(**_SAFE_PRODUCTION)
    assert settings.environment == "production"


def test_development_defaults_are_accepted() -> None:
    settings = Settings(environment="development")
    assert settings.dev_signin_enabled is True
    assert settings.cookie_secure is False


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"dev_signin_enabled": True}, "dev sign-in"),
        ({"cookie_secure": False}, "cookie_secure"),
        ({"webauthn_origin": "http://localhost:3000"}, "https"),
    ],
)
def test_unsafe_production_settings_are_rejected(
    override: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        Settings(**{**_SAFE_PRODUCTION, **override})


def test_environment_default_is_fail_closed() -> None:
    assert Settings.model_fields["environment"].default == "production"


def test_unconfigured_settings_are_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    for key in list(os.environ):
        if key.startswith("RINAVI_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValidationError, match="dev sign-in"):
        Settings()
