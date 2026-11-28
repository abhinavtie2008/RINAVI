import hashlib
import secrets
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.service import emit_audit
from app.modules.identity.models import Session, User, utcnow


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def canonical_email(email: str) -> str:
    return email.strip().lower()


async def find_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_or_create_user(db: AsyncSession, email: str) -> User:
    email = canonical_email(email)
    user = await find_user_by_email(db, email)
    if user is not None:
        return user
    try:
        user = User(email=email, display_name=email.split("@")[0])
        db.add(user)
        await db.flush()
    except IntegrityError:
        # users.email is unique: two sign-ins for the same address can both
        # miss the read above. The loser rolls back and returns the winner's
        # row rather than a 500. Nothing else is written this early in a
        # sign-in, so the rollback discards only the failed insert.
        await db.rollback()
        user = await find_user_by_email(db, email)
        if user is None:
            raise
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


async def revoke_session(db: AsyncSession, token: str) -> uuid.UUID | None:
    result = await db.execute(
        select(Session).where(Session.token_hash == hash_token(token))
    )
    session = result.scalar_one_or_none()
    if session is not None:
        session.revoked_at = utcnow()
        await db.flush()
        return session.user_id
    return None


async def delete_user(db: AsyncSession, user: User) -> None:
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="account.deleted",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email},
    )
    await db.delete(user)
    await db.flush()
