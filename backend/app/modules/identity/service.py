import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.identity.models import Session, User, utcnow


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


async def get_or_create_user(db: AsyncSession, email: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=email, display_name=email.split("@")[0])
        db.add(user)
        await db.flush()
    return user


async def create_session(db: AsyncSession, user: User) -> str:
    settings = get_settings()
    token = new_session_token()
    db.add(
        Session(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=utcnow() + timedelta(hours=settings.session_ttl_hours),
        )
    )
    await db.flush()
    return token


async def get_user_for_token(db: AsyncSession, token: str) -> User | None:
    result = await db.execute(
        select(Session).where(Session.token_hash == hash_token(token))
    )
    session = result.scalar_one_or_none()
    if session is None or session.revoked_at is not None:
        return None
    if session.expires_at < utcnow():
        return None
    return await db.get(User, session.user_id)


async def revoke_session(db: AsyncSession, token: str) -> None:
    result = await db.execute(
        select(Session).where(Session.token_hash == hash_token(token))
    )
    session = result.scalar_one_or_none()
    if session is not None:
        session.revoked_at = utcnow()
        await db.flush()
