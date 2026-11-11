from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.modules.identity import service as identity_service
from app.modules.identity.models import User

DbSession = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(request: Request, db: DbSession) -> User:
    settings = get_settings()
    token = request.cookies.get(settings.cookie_name)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    user = await identity_service.get_user_for_token(db, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
