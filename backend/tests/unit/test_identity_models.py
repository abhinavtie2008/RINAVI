import uuid
from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.db import async_session_factory
from app.modules.identity.models import Session, User, utcnow


async def test_create_user_roundtrip() -> None:
    async with async_session_factory() as db:
        user = User(email="citizen@example.com", display_name="Citizen")
        db.add(user)
        await db.commit()

        fetched = await db.get(User, user.id)
        assert fetched is not None
        assert fetched.email == "citizen@example.com"
        assert fetched.display_name == "Citizen"
        assert fetched.created_at is not None


async def test_session_requires_existing_user() -> None:
    async with async_session_factory() as db:
        db.add(
            Session(
                user_id=uuid.uuid4(),
                token_hash="a" * 64,
                expires_at=utcnow() + timedelta(days=1),
            )
        )
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()
