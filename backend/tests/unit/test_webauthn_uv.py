import base64
import json
import uuid
from typing import Any

from app.modules.identity import webauthn as webauthn_module
from app.modules.identity.models import Credential, User
from app.modules.identity.webauthn import (
    authentication_options,
    registration_options,
    verify_authentication,
)


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _user() -> User:
    return User(
        id=uuid.uuid4(),
        email="citizen@example.com",
        display_name="Citizen",
    )


def test_registration_options_require_user_verification() -> None:
    _challenge_id, options_json = registration_options(_user(), [])
    options = json.loads(options_json)
    assert options["authenticatorSelection"]["userVerification"] == "required"


def test_authentication_options_require_user_verification() -> None:
    _challenge_id, options_json = authentication_options()
    options = json.loads(options_json)
    assert options["userVerification"] == "required"


def test_verify_authentication_enforces_user_verification(
    monkeypatch: Any,
) -> None:
    captured: dict[str, Any] = {}

    class _Verification:
        new_sign_count = 3

    def spy_verify_authentication_response(**kwargs: Any) -> _Verification:
        captured.update(kwargs)
        return _Verification()

    monkeypatch.setattr(
        webauthn_module,
        "verify_authentication_response",
        spy_verify_authentication_response,
    )

    challenge_id, _options = authentication_options()
    user = _user()
    credential_id = b64url(b"cred-1")
    stored = Credential(
        id=uuid.uuid4(),
        user_id=user.id,
        credential_id=credential_id,
        public_key=b64url(b"\x04" + b"\x00" * 64),
        sign_count=0,
    )
    credential_json = json.dumps(
        {
            "id": credential_id,
            "rawId": credential_id,
            "type": "public-key",
            "response": {
                "clientDataJSON": b64url(b'{"type":"webauthn.get"}'),
                "authenticatorData": b64url(b"\x00" * 37),
                "signature": b64url(b"\x00" * 64),
            },
        }
    )

    new_sign_count = verify_authentication(challenge_id, credential_json, stored)

    assert new_sign_count == 3
    assert captured["require_user_verification"] is True
