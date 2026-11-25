import base64
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings

_KEY = base64.urlsafe_b64encode(os.urandom(32)).decode()

_SAFE_PRODUCTION = {
    "environment": "production",
    "dev_signin_enabled": False,
    "cookie_secure": True,
    "webauthn_origin": "https://rinavi.example",
    "storage_encryption_key": _KEY,
}


def test_safe_production_settings_are_accepted() -> None:
    settings = Settings(**_SAFE_PRODUCTION)
    assert settings.environment == "production"


def test_development_settings_are_accepted_with_explicit_dev_signin() -> None:
    settings = Settings(environment="development", dev_signin_enabled=True)
    assert settings.dev_signin_enabled is True
    assert settings.cookie_secure is False


def test_dev_signin_defaults_to_disabled() -> None:
    # Dev sign-in is a sign-in bypass, so it must be opt-in even in
    # development: a forgotten env file must not quietly enable it.
    assert Settings.model_fields["dev_signin_enabled"].default is False


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
    with pytest.raises(ValidationError, match="RINAVI_ENVIRONMENT"):
        Settings()


def test_omitted_environment_is_rejected_even_when_other_values_are_safe(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Without RINAVI_ENVIRONMENT the model silently falls back to production,
    # so a deployment that forgot it used to trip a secondary check and report
    # "dev sign-in must be disabled outside development" — which names the
    # wrong cause. Omission itself must be the reported problem.
    for key in list(os.environ):
        if key.startswith("RINAVI_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)
    safe_without_environment = {
        key: value for key, value in _SAFE_PRODUCTION.items() if key != "environment"
    }
    with pytest.raises(ValidationError, match="RINAVI_ENVIRONMENT"):
        Settings(**safe_without_environment)

def test_production_requires_a_storage_key() -> None:
    # Item 101: a production configuration that would write plaintext blobs
    # must not start at all.
    without_key = {
        key: value
        for key, value in _SAFE_PRODUCTION.items()
        if key != "storage_encryption_key"
    }
    with pytest.raises(ValidationError, match="RINAVI_STORAGE_ENCRYPTION_KEY"):
        Settings(**without_key)


def test_storage_key_decodes_to_32_bytes() -> None:
    settings = Settings(environment="development", storage_encryption_key=_KEY)
    assert len(settings.storage_key() or b"") == 32


def test_development_may_run_without_a_storage_key() -> None:
    assert Settings(environment="development").storage_key() is None


def test_storage_key_must_decode_to_32_bytes() -> None:
    with pytest.raises(ValidationError, match="32 bytes"):
        Settings(
            environment="development",
            storage_encryption_key=base64.urlsafe_b64encode(b"short").decode(),
        )


def test_storage_key_must_be_base64() -> None:
    with pytest.raises(ValidationError, match="base64"):
        Settings(environment="development", storage_encryption_key="not base64!!")


def test_storage_key_file_is_read(tmp_path: Path) -> None:
    path = tmp_path / "blob.key"
    path.write_text(_KEY, encoding="utf-8")

    settings = Settings(environment="development", storage_encryption_key_file=str(path))

    assert len(settings.storage_key() or b"") == 32


def test_storage_key_file_must_be_readable(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="cannot be read"):
        Settings(
            environment="development",
            storage_encryption_key_file=str(tmp_path / "missing.key"),
        )


def test_only_one_storage_key_source_may_be_set() -> None:
    with pytest.raises(ValidationError, match="only one"):
        Settings(
            environment="development",
            storage_encryption_key=_KEY,
            storage_encryption_key_file="blob.key",
        )


def test_storage_key_is_absent_from_repr_and_dump() -> None:
    settings = Settings(environment="development", storage_encryption_key=_KEY)
    assert _KEY not in repr(settings)
    assert _KEY not in str(settings.model_dump())
    assert _KEY not in settings.model_dump_json()
    assert "storage_encryption_key=" not in repr(settings)


def test_invalid_storage_key_is_absent_from_validation_text() -> None:
    bad = "not base64!!"
    with pytest.raises(ValidationError) as caught:
        Settings(environment="development", storage_encryption_key=bad)
    assert bad not in str(caught.value)
    # errors() is not part of the contract we log, but keep the reminder
    # visible here: the raw input survives in it, so nothing may serialise it.
    assert "input" in caught.value.errors()[0]
