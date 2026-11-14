from sqlalchemy import func, select

from app.core.db import async_session_factory
from app.modules.identity import service
from app.modules.identity.models import User


async def test_email_is_canonicalized_before_lookup_and_store() -> None:
    async with async_session_factory() as db:
        user = await service.get_or_create_user(db, "  Citizen@Example.COM ")
        await db.commit()
        assert user.email == "citizen@example.com"


async def test_case_variants_reuse_the_same_user() -> None:
    async with async_session_factory() as db:
        first = await service.get_or_create_user(db, "citizen@example.com")
        await db.commit()
        second = await service.get_or_create_user(db, "CITIZEN@Example.com")
        await db.commit()
        assert second.id == first.id
        result = await db.execute(select(func.count()).select_from(User))
        assert result.scalar_one() == 1
