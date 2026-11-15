import hashlib
from types import SimpleNamespace

import pytest
from starlette.requests import Request

from app.core import rate_limit


def make_request(
    *, headers: dict[str, str] | None = None, host: str = "127.0.0.1"
) -> Request:
    raw_headers = [
        (name.lower().encode("latin-1"), value.encode("latin-1"))
        for name, value in (headers or {}).items()
    ]
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": raw_headers,
            "client": (host, 1234),
            "query_string": b"",
            "server": ("test", 80),
            "scheme": "http",
        }
    )


def test_client_ip_ignores_forwarded_header_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rate_limit, "settings", SimpleNamespace(trust_proxy_headers=False)
    )
    request = make_request(headers={"x-forwarded-for": "203.0.113.7"})

    assert rate_limit.client_ip(request) == "127.0.0.1"


def test_client_ip_uses_first_valid_forwarded_address_when_trusted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rate_limit, "settings", SimpleNamespace(trust_proxy_headers=True)
    )
    request = make_request(
        headers={"x-forwarded-for": "203.0.113.7, 10.0.0.1"}
    )

    assert rate_limit.client_ip(request) == "203.0.113.7"


def test_client_ip_falls_back_for_invalid_forwarded_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rate_limit, "settings", SimpleNamespace(trust_proxy_headers=True)
    )
    request = make_request(headers={"x-forwarded-for": "not-an-address"})

    assert rate_limit.client_ip(request) == "127.0.0.1"


def test_session_key_is_a_stable_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rate_limit,
        "settings",
        SimpleNamespace(
            cookie_name="rinavi_session", trust_proxy_headers=False
        ),
    )
    token = "s3cret-session-token"
    request = make_request(headers={"cookie": f"rinavi_session={token}"})

    key = rate_limit.session_or_ip(request)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()

    assert key == f"session:{digest}"
    assert token not in key


def test_session_keys_differ_per_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rate_limit,
        "settings",
        SimpleNamespace(
            cookie_name="rinavi_session", trust_proxy_headers=False
        ),
    )
    first = make_request(headers={"cookie": "rinavi_session=first"})
    second = make_request(headers={"cookie": "rinavi_session=second"})

    assert rate_limit.session_or_ip(first) != rate_limit.session_or_ip(second)
