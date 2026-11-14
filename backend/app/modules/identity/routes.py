import json

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select
from webauthn.helpers import bytes_to_base64url, parse_authentication_credential_json

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.modules.consent import schemas as consent_schemas
from app.modules.consent import service as consent_service
from app.modules.identity import schemas, service, webauthn
from app.modules.identity.models import Credential, User
from app.modules.vault.storage import get_storage

router = APIRouter(prefix="/auth", tags=["identity"])


@router.post("/dev-signin", response_model=schemas.UserOut)
async def dev_signin(
    payload: schemas.DevSigninRequest,
    response: Response,
    db: DbSession,
) -> schemas.UserOut:
    settings = get_settings()
    if not settings.dev_signin_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    user = await service.get_or_create_user(db, payload.email)
    token = await service.create_session(db, user)
    await db.commit()
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.session_ttl_hours * 3600,
    )
    return schemas.UserOut.model_validate(user)


@router.get("/me", response_model=schemas.UserOut)
async def me(user: CurrentUser) -> schemas.UserOut:
    return schemas.UserOut.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: DbSession) -> None:
    settings = get_settings()
    token = request.cookies.get(settings.cookie_name)
    if token is not None:
        await service.revoke_session(db, token)
        await db.commit()
    response.delete_cookie(settings.cookie_name)


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    response: Response,
    user: CurrentUser,
    db: DbSession,
) -> None:
    settings = get_settings()
    # Erase stored files before dropping the only handle to them. If this
    # fails, keep the account so the citizen can retry the deletion.
    try:
        get_storage().purge_user(user.id)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account data could not be erased; try again",
        ) from exc
    await service.delete_user(db, user)
    await db.commit()
    response.delete_cookie(settings.cookie_name)


@router.get("/export", response_model=schemas.AccountExport)
async def export_account(user: CurrentUser, db: DbSession) -> schemas.AccountExport:
    records = await consent_service.list_own_grants(db, user)
    return schemas.AccountExport(
        user=schemas.UserOut.model_validate(user),
        consent_records=[
            consent_schemas.ConsentRecordOut.model_validate(r) for r in records
        ],
    )


@router.post("/passkey/register/begin")
async def passkey_register_begin(user: CurrentUser, db: DbSession) -> dict:
    result = await db.execute(select(Credential).where(Credential.user_id == user.id))
    existing_ids = [c.credential_id for c in result.scalars()]
    challenge_id, options_json = webauthn.registration_options(user, existing_ids)
    return {"challenge_id": challenge_id, "options": json.loads(options_json)}


@router.post("/passkey/register/finish", status_code=status.HTTP_201_CREATED)
async def passkey_register_finish(
    payload: schemas.PasskeyFinishRequest, user: CurrentUser, db: DbSession
) -> dict:
    try:
        verification = webauthn.verify_registration(payload.challenge_id, payload.credential)
    except webauthn.PasskeyChallengeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except webauthn.PasskeyVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.add(
        Credential(
            user_id=user.id,
            credential_id=bytes_to_base64url(verification.credential_id),
            public_key=bytes_to_base64url(verification.credential_public_key),
            sign_count=verification.sign_count,
        )
    )
    await db.commit()
    return {"status": "registered"}


@router.post("/passkey/login/begin")
async def passkey_login_begin() -> dict:
    challenge_id, options_json = webauthn.authentication_options()
    return {"challenge_id": challenge_id, "options": json.loads(options_json)}


@router.post("/passkey/login/finish", response_model=schemas.UserOut)
async def passkey_login_finish(
    payload: schemas.PasskeyFinishRequest, response: Response, db: DbSession
) -> schemas.UserOut:
    settings = get_settings()
    try:
        credential = parse_authentication_credential_json(
            payload.credential
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credential"
        ) from exc

    result = await db.execute(
        select(Credential).where(
            Credential.credential_id == bytes_to_base64url(credential.raw_id)
        )
    )
    stored = result.scalar_one_or_none()
    if stored is None:
        webauthn.pop_challenge(payload.challenge_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown credential"
        )

    try:
        new_sign_count = webauthn.verify_authentication(
            payload.challenge_id, payload.credential, stored
        )
    except webauthn.PasskeyChallengeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except webauthn.PasskeyVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    stored.sign_count = new_sign_count
    user = await db.get(User, stored.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists"
        )
    token = await service.create_session(db, user)
    await db.commit()
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.session_ttl_hours * 3600,
    )
    return schemas.UserOut.model_validate(user)
