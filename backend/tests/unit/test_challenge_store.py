from collections.abc import Iterator

import pytest

from app.modules.identity import webauthn


@pytest.fixture(autouse=True)
def _clear_challenges() -> Iterator[None]:
    webauthn._pending_challenges.clear()
    yield
    webauthn._pending_challenges.clear()


def test_challenge_is_single_use() -> None:
    challenge_id, challenge = webauthn._issue_challenge()
    assert webauthn.pop_challenge(challenge_id) == challenge
    assert webauthn.pop_challenge(challenge_id) is None


def test_expired_challenge_is_rejected() -> None:
    challenge_id, challenge = webauthn._issue_challenge()
    webauthn._pending_challenges[challenge_id] = (challenge, 0.0)
    assert webauthn.pop_challenge(challenge_id) is None
    assert challenge_id not in webauthn._pending_challenges


def test_store_evicts_oldest_challenge_at_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(webauthn, "_MAX_PENDING_CHALLENGES", 2)
    first, _ = webauthn._issue_challenge()
    second, _ = webauthn._issue_challenge()
    third, _ = webauthn._issue_challenge()
    assert first not in webauthn._pending_challenges
    assert second in webauthn._pending_challenges
    assert third in webauthn._pending_challenges
    assert len(webauthn._pending_challenges) == 2
