from httpx import ASGITransport, AsyncClient, Cookies

from app.main import app

API = "/api/v1"

INCOME_TEXT = (
    "Applicant Name: Asha Devi\n"
    "Father's Name: Rajesh Devi\n"
    "Date of Birth: 12/03/1994\n"
    "Gender: Female\n"
    "Address: 14, Nehru Colony, Example Nagar\n"
    "Annual Income: Rs. 1,20,000\n"
    "Aadhaar: 1234 5678 9012\n"
)


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=Cookies(),
    )


async def sign_in(client: AsyncClient, email: str = "citizen@example.com") -> None:
    response = await client.post(f"{API}/auth/dev-signin", json={"email": email})
    assert response.status_code == 200


async def allow(client: AsyncClient, purpose: str) -> None:
    response = await client.post(f"{API}/consent/grants", json={"purpose": purpose})
    assert response.status_code == 201


async def upload_income_document(client: AsyncClient) -> str:
    response = await client.post(
        f"{API}/vault/documents",
        files={"file": ("income.txt", INCOME_TEXT.encode(), "text/plain")},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "processed"
    return response.json()["id"]


async def promote(client: AsyncClient, document_id: str):
    return await client.post(
        f"{API}/profile/values/promote", json={"document_id": document_id}
    )


async def test_promote_requires_profile_consent() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        document_id = await upload_income_document(client)

        response = await promote(client, document_id)

        assert response.status_code == 403


async def test_promote_creates_unconfirmed_source_linked_values() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "profile.storage")
        document_id = await upload_income_document(client)

        response = await promote(client, document_id)

        assert response.status_code == 200
        values = response.json()
        assert len(values) == 7
        assert {v["field_key"] for v in values} == {
            "full_name",
            "father_name",
            "date_of_birth",
            "gender",
            "address",
            "annual_income",
            "aadhaar_number",
        }
        assert {v["status"] for v in values} == {"unconfirmed"}
        full_name = next(v for v in values if v["field_key"] == "full_name")
        assert full_name["value"] == "Asha Devi"
        assert full_name["source_document_id"] == document_id
        assert full_name["source_locator"] == "line 1"
        assert full_name["confidence"] == "high"

        listed = await client.get(f"{API}/profile/values")
        assert [v["id"] for v in listed.json()] == [v["id"] for v in values]


async def test_correction_confirms_and_records_history() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "profile.storage")
        document_id = await upload_income_document(client)
        values = (await promote(client, document_id)).json()
        full_name = next(v for v in values if v["field_key"] == "full_name")

        corrected = await client.post(
            f"{API}/profile/values/{full_name['id']}/correct",
            json={"value": "Asha Devi Sharma"},
        )

        assert corrected.status_code == 200
        body = corrected.json()
        assert body["value"] == "Asha Devi Sharma"
        assert body["status"] == "confirmed"
        assert body["correction_history"] == [
            {
                "old_value": "Asha Devi",
                "corrected_at": body["correction_history"][0]["corrected_at"],
            }
        ]


async def test_confirm_only_from_unconfirmed() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "profile.storage")
        document_id = await upload_income_document(client)
        values = (await promote(client, document_id)).json()
        dob = next(v for v in values if v["field_key"] == "date_of_birth")

        confirmed = await client.post(f"{API}/profile/values/{dob['id']}/confirm")
        assert confirmed.status_code == 200
        assert confirmed.json()["status"] == "confirmed"

        again = await client.post(f"{API}/profile/values/{dob['id']}/confirm")
        assert again.status_code == 409


async def test_repromote_never_overwrites_confirmed_values() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "profile.storage")
        document_id = await upload_income_document(client)
        values = (await promote(client, document_id)).json()
        full_name = next(v for v in values if v["field_key"] == "full_name")
        await client.post(
            f"{API}/profile/values/{full_name['id']}/correct",
            json={"value": "Asha Devi Sharma"},
        )

        repromoted = (await promote(client, document_id)).json()

        after = next(v for v in repromoted if v["field_key"] == "full_name")
        assert after["value"] == "Asha Devi Sharma"
        assert after["status"] == "confirmed"
        assert len(repromoted) == 7


async def test_reject_removes_unconfirmed_but_not_confirmed() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "profile.storage")
        document_id = await upload_income_document(client)
        values = (await promote(client, document_id)).json()
        gender = next(v for v in values if v["field_key"] == "gender")
        full_name = next(v for v in values if v["field_key"] == "full_name")
        await client.post(f"{API}/profile/values/{full_name['id']}/confirm")

        rejected = await client.post(f"{API}/profile/values/{gender['id']}/reject")
        assert rejected.status_code == 204

        remaining = (await client.get(f"{API}/profile/values")).json()
        assert {v["field_key"] for v in remaining} == {
            "full_name",
            "father_name",
            "date_of_birth",
            "address",
            "annual_income",
            "aadhaar_number",
        }

        blocked = await client.post(f"{API}/profile/values/{full_name['id']}/reject")
        assert blocked.status_code == 409


async def test_promote_requires_a_processed_document() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "profile.storage")
        response = await client.post(
            f"{API}/vault/documents",
            files={"file": ("scan.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 32, "image/png")},
        )
        document_id = response.json()["id"]

        promoted = await promote(client, document_id)

        assert promoted.status_code == 409


async def test_profile_is_scoped_to_the_owner() -> None:
    async with make_client() as alice:
        await sign_in(alice, "alice@example.com")
        await allow(alice, "documents.processing")
        await allow(alice, "profile.storage")
        document_id = await upload_income_document(alice)
        values = (await promote(alice, document_id)).json()
        value_id = values[0]["id"]
        document_id_alice = document_id

        async with make_client() as bob:
            await sign_in(bob, "bob@example.com")
            await allow(bob, "documents.processing")
            await allow(bob, "profile.storage")

            assert (await bob.get(f"{API}/profile/values")).json() == []
            assert (
                await bob.post(f"{API}/profile/values/{value_id}/confirm")
            ).status_code == 404
            assert (await promote(bob, document_id_alice)).status_code == 404


async def test_reject_works_without_active_consent() -> None:
    async with make_client() as client:
        await sign_in(client)
        await allow(client, "documents.processing")
        await allow(client, "profile.storage")
        document_id = await upload_income_document(client)
        values = (await promote(client, document_id)).json()

        grants = (await client.get(f"{API}/consent/grants")).json()
        active = next(
            g
            for g in grants
            if g["purpose"] == "profile.storage" and g["withdrawn_at"] is None
        )
        await client.post(f"{API}/consent/grants/{active['id']}/withdraw")

        response = await client.post(f"{API}/profile/values/{values[0]['id']}/reject")
        assert response.status_code == 204
