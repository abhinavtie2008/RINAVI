from httpx import ASGITransport, AsyncClient, Cookies

from app.main import app
from app.modules.consent.purposes import CONSENT_PURPOSES


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=Cookies(),
    )


async def sign_in(client: AsyncClient, email: str) -> None:
    response = await client.post("/api/v1/auth/dev-signin", json={"email": email})
    assert response.status_code == 200


async def test_grant_then_list_shows_active_record() -> None:
    async with make_client() as client:
        await sign_in(client, "citizen@example.com")

        granted = await client.post(
            "/api/v1/consent/grants", json={"purpose": "documents.processing"}
        )
        assert granted.status_code == 201
        body = granted.json()
        assert body["purpose"] == "documents.processing"
        assert body["policy_version"] == "1.0"
        assert body["withdrawn_at"] is None

        listed = await client.get("/api/v1/consent/grants")
        assert listed.status_code == 200
        assert [r["id"] for r in listed.json()] == [body["id"]]


async def test_withdraw_marks_record_then_regrant_creates_new_record() -> None:
    async with make_client() as client:
        await sign_in(client, "citizen@example.com")
        granted = await client.post(
            "/api/v1/consent/grants", json={"purpose": "documents.processing"}
        )
        consent_id = granted.json()["id"]

        withdrawn = await client.post(f"/api/v1/consent/grants/{consent_id}/withdraw")
        assert withdrawn.status_code == 200
        assert withdrawn.json()["withdrawn_at"] is not None

        regranted = await client.post(
            "/api/v1/consent/grants", json={"purpose": "documents.processing"}
        )
        assert regranted.status_code == 201
        assert regranted.json()["id"] != consent_id

        listed = await client.get("/api/v1/consent/grants")
        records = listed.json()
        assert len(records) == 2
        assert [r["withdrawn_at"] is None for r in records] == [True, False]


async def test_cross_user_cannot_see_or_withdraw() -> None:
    async with make_client() as client_a:
        await sign_in(client_a, "alice@example.com")
        granted = await client_a.post(
            "/api/v1/consent/grants", json={"purpose": "documents.processing"}
        )
        alice_consent_id = granted.json()["id"]

        async with make_client() as client_b:
            await sign_in(client_b, "bob@example.com")

            listed = await client_b.get("/api/v1/consent/grants")
            assert listed.status_code == 200
            assert listed.json() == []

            taken = await client_b.post(
                f"/api/v1/consent/grants/{alice_consent_id}/withdraw"
            )
            assert taken.status_code == 404


async def test_grant_rejects_blank_purpose() -> None:
    async with make_client() as client:
        await sign_in(client, "citizen@example.com")
        for purpose in ("", "   "):
            response = await client.post(
                "/api/v1/consent/grants", json={"purpose": purpose}
            )
            assert response.status_code == 422


async def test_grant_accepts_each_documented_purpose() -> None:
    # The four strings are hardcoded: iterating CONSENT_PURPOSES would read the
    # same tuple the validator reads, so adding a fifth purpose there would keep
    # this test green while the API started accepting it.
    async with make_client() as client:
        await sign_in(client, "citizen@example.com")
        for purpose in (
            "documents.processing",
            "profile.storage",
            "applications.preparation",
            "locker.tracking",
        ):
            granted = await client.post(
                "/api/v1/consent/grants", json={"purpose": purpose}
            )
            assert granted.status_code == 201, purpose
            assert granted.json()["purpose"] == purpose


async def test_grant_rejects_purposes_outside_the_data_map() -> None:
    # Only the four purposes in docs/compliance/data-map.md §4 exist. An
    # unknown or differently-cased one must be refused before it is written,
    # so the table the reviewer sees is the table the database holds.
    async with make_client() as client:
        await sign_in(client, "citizen@example.com")
        for purpose in (
            "marketing",
            "Documents.Processing",
            "documents.processing.v2",
            "documents",
        ):
            response = await client.post(
                "/api/v1/consent/grants", json={"purpose": purpose}
            )
            assert response.status_code == 422, purpose
            message = response.json()["detail"][0]["msg"]
            assert "Accepted values" in message
            for accepted in CONSENT_PURPOSES:
                assert accepted in message

        listed = await client.get("/api/v1/consent/grants")
        assert listed.json() == []


async def test_grant_and_withdraw_emit_audit_events() -> None:
    from sqlalchemy import select

    from app.core.db import async_session_factory
    from app.modules.audit.models import AuditEvent

    async with make_client() as client:
        sign_in_response = await client.post(
            "/api/v1/auth/dev-signin", json={"email": "citizen@example.com"}
        )
        user_id = sign_in_response.json()["id"]

        granted = await client.post(
            "/api/v1/consent/grants", json={"purpose": "documents.processing"}
        )
        consent_id = granted.json()["id"]
        await client.post(f"/api/v1/consent/grants/{consent_id}/withdraw")

    async with async_session_factory() as db:
        events = (await db.execute(select(AuditEvent))).scalars().all()
        granted_events = [e for e in events if e.action == "consent.granted"]
        withdrawn_events = [e for e in events if e.action == "consent.withdrawn"]

        assert len(granted_events) == 1
        assert str(granted_events[0].actor_user_id) == user_id
        assert granted_events[0].resource_type == "consent_record"
        assert granted_events[0].resource_id == consent_id
        assert granted_events[0].details == {"purpose": "documents.processing"}

        assert len(withdrawn_events) == 1
        assert str(withdrawn_events[0].actor_user_id) == user_id
        assert withdrawn_events[0].resource_id == consent_id


async def test_unauthenticated_gets_401() -> None:
    async with make_client() as client:
        assert (await client.get("/api/v1/consent/grants")).status_code == 401
        assert (
            await client.post(
                "/api/v1/consent/grants", json={"purpose": "documents.processing"}
            )
        ).status_code == 401
