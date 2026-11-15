import importlib.util
from pathlib import Path
from typing import Any

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "ai_review.py"


def _load_ai_review() -> Any:
    spec = importlib.util.spec_from_file_location("ai_review", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ai_review = _load_ai_review()


def test_version_key_handles_missing_minor() -> None:
    assert ai_review._version_key("gemini-3-flash") == (3, 0)
    assert ai_review._version_key("gemini-3.8-flash") == (3, 8)
    assert ai_review._version_key("not-a-gemini-model") == (0, 0)


def test_pick_models_prefers_newest_stable_flash() -> None:
    models = [
        "gemini-2.5-flash",
        "gemini-3.8-flash",
        "gemini-3.9-flash-preview",
        "gemini-3.0-pro",
        "text-embedding-004",
    ]

    ordered = ai_review.pick_models(models)

    assert ordered[:2] == ["gemini-3.8-flash", "gemini-2.5-flash"]
    assert "gemini-3.9-flash-preview" in ordered
    assert "gemini-3.0-pro" not in ordered
    assert "text-embedding-004" not in ordered


def test_build_prompt_includes_policy_files(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ai_review, "read_optional", lambda path: f"RULES:{path}")

    prompt = ai_review.build_prompt("diff --git a/x b/x")

    assert "RULES:AGENTS.md" in prompt
    assert "RULES:SECURITY.md" in prompt
    assert "diff --git a/x b/x" in prompt


def test_build_prompt_truncates_oversized_diffs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ai_review, "read_optional", lambda path: "")

    prompt = ai_review.build_prompt("x" * (ai_review.MAX_DIFF_CHARS + 10))

    assert "x" * ai_review.MAX_DIFF_CHARS in prompt
    assert "x" * (ai_review.MAX_DIFF_CHARS + 1) not in prompt
    assert "[Diff truncated for length" in prompt


def test_upsert_comment_updates_existing_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, Any, str | None]] = []

    def fake_request(
        url: str,
        *,
        data: Any = None,
        headers: Any = None,
        method: str | None = None,
    ) -> Any:
        calls.append((url, data, method))
        if data is None:
            return [{"id": 7, "body": f"{ai_review.COMMENT_MARKER} old"}]
        return {}

    monkeypatch.setattr(ai_review, "request_json", fake_request)

    ai_review.upsert_comment("owner/repo", "12", "token", "new body")

    assert calls[0][0].endswith("/issues/12/comments?per_page=100")
    assert calls[1][0].endswith("/issues/comments/7")
    assert calls[1][2] == "PATCH"


def test_upsert_comment_posts_when_marker_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, Any, str | None]] = []

    def fake_request(
        url: str,
        *,
        data: Any = None,
        headers: Any = None,
        method: str | None = None,
    ) -> Any:
        calls.append((url, data, method))
        return [] if data is None else {}

    monkeypatch.setattr(ai_review, "request_json", fake_request)

    ai_review.upsert_comment("owner/repo", "12", "token", "new body")

    assert calls[-1][0].endswith("/issues/12/comments")
    assert calls[-1][2] is None
