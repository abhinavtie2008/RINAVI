from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.modules.identity import schemas, service

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
