from sqlalchemy import func, select

from app.core.db import async_session_factory
from app.modules.identity import service
from app.modules.identity.models import User


async def test_email_is_canonicalized_before_lookup_and_store() -> None:
    async with async_session_factory() as db:
        user = await service.get_or_create_user(db, "  Citizen@Example.COM ")
        await db.commit()
        assert user.email == "citizen@example.com"


async def test_a_lost_sign_in_race_returns_the_winner(monkeypatch) -> None:
    # Two dev sign-ins for one address can both miss the read and then collide
    # on the unique users.email. The loser must return the winner's row, not a
    # 500 and not a second user.
    async with async_session_factory() as db:
        first = await service.get_or_create_user(db, "citizen@example.com")
        await db.commit()
        first_id = first.id

        original = service.find_user_by_email
        calls = {"n": 0}

        async def miss_once(session, email):
            calls["n"] += 1
            if calls["n"] == 1:
                return None
            return await original(session, email)

        monkeypatch.setattr(service, "find_user_by_email", miss_once)

        second = await service.get_or_create_user(db, "citizen@example.com")
        await db.commit()

        assert second.id == first_id
        assert calls["n"] == 2
        result = await db.execute(select(func.count()).select_from(User))
        assert result.scalar_one() == 1


async def test_case_variants_reuse_the_same_user() -> None:
    async with async_session_factory() as db:
        first = await service.get_or_create_user(db, "citizen@example.com")
        await db.commit()
        second = await service.get_or_create_user(db, "CITIZEN@Example.com")
        await db.commit()
        assert second.id == first.id
        result = await db.execute(select(func.count()).select_from(User))
        assert result.scalar_one() == 1
