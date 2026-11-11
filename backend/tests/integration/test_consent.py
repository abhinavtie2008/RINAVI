from httpx import ASGITransport, AsyncClient, Cookies

from app.main import app


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


async def test_unauthenticated_gets_401() -> None:
    async with make_client() as client:
        assert (await client.get("/api/v1/consent/grants")).status_code == 401
        assert (
            await client.post(
                "/api/v1/consent/grants", json={"purpose": "documents.processing"}
            )
        ).status_code == 401
