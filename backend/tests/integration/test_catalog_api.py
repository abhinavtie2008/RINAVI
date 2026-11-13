from httpx import ASGITransport, AsyncClient, Cookies

from app.main import app

API = "/api/v1"


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", cookies=Cookies()
    )


async def sign_in(client: AsyncClient) -> None:
    response = await client.post(
        f"{API}/auth/dev-signin", json={"email": "citizen@example.com"}
    )
    assert response.status_code == 200


async def test_catalog_requires_session() -> None:
    async with make_client() as client:
        assert (await client.get(f"{API}/catalog/services")).status_code == 401


async def test_catalog_lists_delhi_income_certificate() -> None:
    async with make_client() as client:
        await sign_in(client)
        response = await client.get(f"{API}/catalog/services")
        assert response.status_code == 200
        assert {s["slug"] for s in response.json()} >= {"delhi-income-certificate"}


async def test_catalog_detail_includes_pack_and_notice() -> None:
    async with make_client() as client:
        await sign_in(client)
        response = await client.get(
            f"{API}/catalog/services/delhi-income-certificate"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["fields"][0]["id"] == "applicant_name"
        assert body["checklist_groups"][0]["id"] == "identity_proof"
        assert "not submit applications" in body["guidance"]["not_a_submission_notice"]
        assert body["declaration"]["required"] is True


async def test_catalog_unknown_service_is_404() -> None:
    async with make_client() as client:
        await sign_in(client)
        assert (
            await client.get(f"{API}/catalog/services/not-a-service")
        ).status_code == 404
