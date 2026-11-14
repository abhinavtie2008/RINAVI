import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.db import async_session_factory
from app.modules.applications.models import ApplicationDraft
from app.modules.identity.models import User
from app.modules.locker.models import ApplicationCase, CaseEvent


def make_draft(user: User) -> ApplicationDraft:
    return ApplicationDraft(
        user_id=user.id,
        service_slug="delhi-income-certificate",
        service_name="Income Certificate (Delhi)",
        pack_version="1.0.0",
        template_snapshot={"fields": [], "declaration": {}, "checklist_groups": [], "guidance": {}},
        values={},
        document_links={},
        declaration_confirmed=False,
    )


def make_case(
    user: User, draft: ApplicationDraft | None = None, **overrides: object
) -> ApplicationCase:
    return ApplicationCase(
        user_id=user.id,
        draft_id=draft.id if draft is not None else None,
        service_slug="delhi-income-certificate",
        service_name="Income Certificate (Delhi)",
        pack_version="1.0.0",
        packet_snapshot={"fields": []},
        packet_text="RINAVI — application draft (NOT a submission)",
        **overrides,
    )


async def test_case_roundtrip_defaults_to_prepared() -> None:
    async with async_session_factory() as db:
        user = User(email="citizen@example.com", display_name="Citizen")
        db.add(user)
        await db.flush()
        draft = make_draft(user)
        db.add(draft)
        await db.flush()
        case = make_case(user, draft)
        db.add(case)
        await db.commit()

    async with async_session_factory() as db:
        fetched = await db.get(ApplicationCase, case.id)
        assert fetched is not None
        assert fetched.status == "prepared"
        assert fetched.reference_number is None
        assert fetched.acknowledgement_number is None
        assert fetched.deadline_at is None
        assert fetched.outcome_notes is None
        assert fetched.created_at is not None
        assert fetched.updated_at is not None


async def test_case_draft_id_is_unique() -> None:
    async with async_session_factory() as db:
        user = User(email="citizen@example.com", display_name="Citizen")
        db.add(user)
        await db.flush()
        draft = make_draft(user)
        db.add(draft)
        await db.flush()
        db.add(make_case(user, draft))
        await db.flush()
        db.add(make_case(user, draft))
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()


async def test_case_requires_existing_user() -> None:
    async with async_session_factory() as db:
        db.add(
            ApplicationCase(
                user_id=uuid.uuid4(),
                service_slug="delhi-income-certificate",
                service_name="Income Certificate (Delhi)",
                pack_version="1.0.0",
                packet_snapshot={},
                packet_text="text",
            )
        )
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()


async def test_deleting_draft_sets_case_draft_id_null() -> None:
    async with async_session_factory() as db:
        user = User(email="citizen@example.com", display_name="Citizen")
        db.add(user)
        await db.flush()
        draft = make_draft(user)
        db.add(draft)
        await db.flush()
        case = make_case(user, draft)
        db.add(case)
        await db.commit()

        await db.delete(draft)
        await db.commit()
        await db.refresh(case)
        assert case.draft_id is None


async def test_deleting_user_cascades_to_cases_and_events() -> None:
    async with async_session_factory() as db:
        user = User(email="citizen@example.com", display_name="Citizen")
        db.add(user)
        await db.flush()
        case = make_case(user)
        db.add(case)
        await db.flush()
        db.add(CaseEvent(case_id=case.id, type="created", payload={}))
        await db.commit()

        await db.delete(user)
        await db.commit()

        cases = (await db.execute(select(ApplicationCase))).scalars().all()
        events = (await db.execute(select(CaseEvent))).scalars().all()
        assert cases == []
        assert events == []
