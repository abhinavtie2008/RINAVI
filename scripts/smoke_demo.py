#!/usr/bin/env python
"""End-to-end smoke test for the RINAVI demo stack (synthetic data only).

Walks the full citizen flow against a running backend over HTTP: health,
dev sign-in, consent grants, upload of two synthetic PDFs generated in
memory, the A1 check that Aadhaar never reaches profile values, promotion
and confirmation of profile values, creation of a Delhi income-certificate
draft, evidence linking, the declaration, and the export.

Usage:
    python scripts/smoke_demo.py [base_url]

Defaults to http://localhost:8000. Exits non-zero if any step fails.
Run with the backend virtualenv (needs httpx).
"""

import argparse
import sys
import time
from typing import Any, Callable

import httpx

API = "/api/v1"

INCOME_LINES = [
    "Applicant Name: Asha Devi",
    # No apostrophe: pypdf decodes the 0x27 byte as a replacement character
    # in StandardEncoding, so "Father's Name" would never match the pattern.
    "Father Name: Rajesh Devi",
    "Date of Birth: 12/03/1994",
    "Gender: Female",
    "Address: 14, Nehru Colony, Example Nagar",
    "Annual Income: Rs. 1,20,000",
    "Aadhaar: 1234 5678 9012",
]

IDENTITY_LINES = [
    "Applicant Name: Asha Devi",
    "Father Name: Rajesh Devi",
    "Date of Birth: 12/03/1994",
    "Gender: Female",
    "Aadhaar: 1234 5678 9012",
]


def make_text_pdf(lines: list[str]) -> bytes:
    """Minimal single-page PDF with a text layer (same shape as the tests)."""
    content = ["BT", "/F1 12 Tf", "72 760 Td", "14 TL"]
    for line in lines:
        escaped = line.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        content.append(f"({escaped}) Tj T*")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        (
            b"<< /Length "
            + str(len(stream)).encode()
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_start = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_start}\n%%EOF\n"
    ).encode()
    return bytes(out)


class Demo:
    def __init__(self, base_url: str) -> None:
        # trust_env=False keeps localhost traffic off any system proxy, and
        # sidesteps httpx 0.28 crashing on NO_PROXY lists that contain bare
        # IPv6 entries such as "[::1]" or "::1".
        self.client = httpx.Client(base_url=base_url, timeout=30.0, trust_env=False)
        self.email = f"demo+{int(time.time())}@example.com"
        self.income_id: str = ""
        self.identity_id: str = ""
        self.draft_id: str = ""
        self.profile_values: list[dict[str, Any]] = []

    def close(self) -> None:
        self.client.close()


def step_health(demo: Demo) -> None:
    response = demo.client.get(f"{API}/health")
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    assert response.json() == {"status": "ok"}, f"unexpected body: {response.text}"


def step_dev_signin(demo: Demo) -> None:
    response = demo.client.post(f"{API}/auth/dev-signin", json={"email": demo.email})
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    assert response.json()["email"] == demo.email


def step_consents(demo: Demo) -> None:
    for purpose in (
        "documents.processing",
        "profile.storage",
        "applications.preparation",
    ):
        response = demo.client.post(f"{API}/consent/grants", json={"purpose": purpose})
        assert response.status_code == 201, (
            f"{purpose}: expected 201, got {response.status_code}: {response.text[:200]}"
        )


def _upload(demo: Demo, filename: str, lines: list[str]) -> dict[str, Any]:
    response = demo.client.post(
        f"{API}/vault/documents",
        files={"file": (filename, make_text_pdf(lines), "application/pdf")},
    )
    assert response.status_code == 201, (
        f"expected 201, got {response.status_code}: {response.text[:200]}"
    )
    return response.json()


def step_upload_income(demo: Demo) -> None:
    document = _upload(demo, "income.pdf", INCOME_LINES)
    assert document["status"] == "processed", f"status: {document['status']}"
    assert document["classification"] == "income", (
        f"classification: {document['classification']}"
    )
    demo.income_id = document["id"]


def step_upload_identity(demo: Demo) -> None:
    document = _upload(demo, "identity.pdf", IDENTITY_LINES)
    assert document["status"] == "processed", f"status: {document['status']}"
    assert document["classification"] == "identity", (
        f"classification: {document['classification']}"
    )
    demo.identity_id = document["id"]


def step_identity_aadhaar_check(demo: Demo) -> None:
    response = demo.client.get(f"{API}/vault/documents/{demo.identity_id}/fields")
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    fields = response.json()
    assert fields, "identity document should have extracted fields"
    keys = {field["field_key"] for field in fields}
    assert "aadhaar_number" not in keys, (
        f"A1 violation: aadhaar_number present in {sorted(keys)}"
    )


def step_promote(demo: Demo) -> None:
    response = demo.client.post(
        f"{API}/profile/values/promote", json={"document_id": demo.income_id}
    )
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    values = response.json()
    by_key = {value["field_key"]: value for value in values}
    assert by_key.get("full_name", {}).get("value") == "Asha Devi", (
        f"full_name: {by_key.get('full_name')}"
    )
    assert by_key.get("annual_income", {}).get("value") == "120000", (
        f"annual_income: {by_key.get('annual_income')}"
    )
    assert "aadhaar_number" not in by_key, (
        f"A1 violation: aadhaar_number present in {sorted(by_key)}"
    )
    demo.profile_values = values


def step_confirm_values(demo: Demo) -> None:
    assert demo.profile_values, "no profile values to confirm (promote step failed)"
    for value in demo.profile_values:
        response = demo.client.post(f"{API}/profile/values/{value['id']}/confirm")
        assert response.status_code == 200, (
            f"{value['field_key']}: expected 200, got {response.status_code}"
        )
        assert response.json()["status"] == "confirmed"


def step_profile_aadhaar_check(demo: Demo) -> None:
    response = demo.client.get(f"{API}/profile/values")
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    keys = {value["field_key"] for value in response.json()}
    assert "aadhaar_number" not in keys, (
        f"A1 violation: aadhaar_number present in {sorted(keys)}"
    )
    assert {value["status"] for value in response.json()} == {"confirmed"}


def step_create_draft(demo: Demo) -> None:
    response = demo.client.post(
        f"{API}/applications/drafts", json={"service_slug": "delhi-income-certificate"}
    )
    assert response.status_code == 201, f"expected 201, got {response.status_code}"
    draft = response.json()
    demo.draft_id = draft["id"]
    values = draft["values"]
    assert values.get("applicant_name") == {"value": "Asha Devi", "origin": "profile"}, (
        f"applicant_name: {values.get('applicant_name')}"
    )
    assert values.get("annual_income", {}).get("origin") == "profile", (
        f"annual_income: {values.get('annual_income')}"
    )


def step_set_purpose(demo: Demo) -> None:
    response = demo.client.put(
        f"{API}/applications/drafts/{demo.draft_id}/fields/purpose",
        json={"value": "Scholarship application"},
    )
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    assert response.json()["values"]["purpose"] == {
        "value": "Scholarship application",
        "origin": "citizen",
    }


def step_link_evidence(demo: Demo) -> None:
    for group_id, document_id in (
        ("income_evidence", demo.income_id),
        ("identity_proof", demo.identity_id),
        ("residence_proof", demo.identity_id),
    ):
        response = demo.client.put(
            f"{API}/applications/drafts/{demo.draft_id}/documents/{document_id}",
            json={"group_id": group_id},
        )
        assert response.status_code == 200, (
            f"{group_id}: expected 200, got {response.status_code}: {response.text[:200]}"
        )


def step_declaration(demo: Demo) -> None:
    response = demo.client.put(
        f"{API}/applications/drafts/{demo.draft_id}/declaration",
        json={"confirmed": True},
    )
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    draft = response.json()
    assert draft["declaration_confirmed"] is True
    assert draft["validation"] == [], f"unresolved issues: {draft['validation']}"


def step_export(demo: Demo) -> None:
    response = demo.client.get(f"{API}/applications/drafts/{demo.draft_id}/export")
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    text = response.json()["text"]
    for expected in ("NOT a submission", "Asha Devi", "income.pdf", "Declaration: CONFIRMED"):
        assert expected in text, f"export text missing {expected!r}"


STEPS: list[tuple[str, Callable[[Demo], None]]] = [
    ("health endpoint", step_health),
    ("dev sign-in", step_dev_signin),
    ("consent grants", step_consents),
    ("upload income.pdf", step_upload_income),
    ("upload identity.pdf", step_upload_identity),
    ("identity fields never include Aadhaar", step_identity_aadhaar_check),
    ("promote income values to profile", step_promote),
    ("confirm profile values", step_confirm_values),
    ("profile values never include Aadhaar", step_profile_aadhaar_check),
    ("create income-certificate draft", step_create_draft),
    ("set draft purpose", step_set_purpose),
    ("link evidence documents", step_link_evidence),
    ("confirm declaration", step_declaration),
    ("export the draft", step_export),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", nargs="?", default="http://localhost:8000")
    args = parser.parse_args()

    demo = Demo(args.base_url)
    failures: list[str] = []
    try:
        for label, step in STEPS:
            try:
                step(demo)
                print(f"PASS  {label}")
            except AssertionError as exc:
                failures.append(label)
                print(f"FAIL  {label}: {exc}")
            except httpx.HTTPError as exc:
                failures.append(label)
                print(f"FAIL  {label}: {exc.__class__.__name__}: {exc}")
    finally:
        demo.close()

    print()
    if failures:
        print(f"{len(failures)} of {len(STEPS)} steps failed.")
        return 1
    print(f"All {len(STEPS)} steps passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
