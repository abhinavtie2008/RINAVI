import secrets
from typing import Any

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import (
    base64url_to_bytes,
    options_to_json,
    parse_authentication_credential_json,
    parse_registration_credential_json,
)
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.core.config import get_settings
from app.modules.identity.models import Credential, User

_pending_challenges: dict[str, bytes] = {}


class PasskeyChallengeError(Exception):
    pass


class PasskeyVerificationError(Exception):
    pass


def _issue_challenge() -> tuple[str, bytes]:
    challenge_id = secrets.token_urlsafe(24)
    _pending_challenges[challenge_id] = secrets.token_bytes(32)
    return challenge_id, _pending_challenges[challenge_id]


def pop_challenge(challenge_id: str) -> bytes | None:
    return _pending_challenges.pop(challenge_id, None)


def registration_options(
    user: User, exclude_credential_ids: list[str]
) -> tuple[str, str]:
    settings = get_settings()
    challenge_id, challenge = _issue_challenge()
    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=user.id.bytes,
        user_name=user.email,
        user_display_name=user.display_name,
        challenge=challenge,
        attestation=AttestationConveyancePreference.NONE,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(cid))
            for cid in exclude_credential_ids
        ],
    )
    return challenge_id, options_to_json(options)


def authentication_options() -> tuple[str, str]:
    settings = get_settings()
    challenge_id, challenge = _issue_challenge()
    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        challenge=challenge,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    return challenge_id, options_to_json(options)


def verify_registration(challenge_id: str, credential_json: str) -> Any:
    settings = get_settings()
    challenge = pop_challenge(challenge_id)
    if challenge is None:
        raise PasskeyChallengeError("Unknown or expired challenge")
    try:
        credential = parse_registration_credential_json(credential_json)
        return verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_origin=settings.webauthn_origin,
            expected_rp_id=settings.webauthn_rp_id,
        )
    except Exception as exc:
        raise PasskeyVerificationError(str(exc)) from exc


def verify_authentication(
    challenge_id: str, credential_json: str, stored: Credential
) -> int:
    settings = get_settings()
    challenge = pop_challenge(challenge_id)
    if challenge is None:
        raise PasskeyChallengeError("Unknown or expired challenge")
    try:
        credential = parse_authentication_credential_json(credential_json)
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_origin=settings.webauthn_origin,
            expected_rp_id=settings.webauthn_rp_id,
            credential_public_key=base64url_to_bytes(stored.public_key),
            credential_current_sign_count=stored.sign_count,
        )
        return verification.new_sign_count
    except Exception as exc:
        raise PasskeyVerificationError(str(exc)) from exc
