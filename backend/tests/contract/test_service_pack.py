import json
from pathlib import Path
from typing import Any

from app.modules.documents.extraction import FIELD_KEYS

CATALOG_ROOT = Path(__file__).resolve().parents[3] / "catalog" / "services"
SERVICE_DIR = CATALOG_ROOT / "edistrict" / "income-certificate"


def load_service() -> dict[str, Any]:
    with open(SERVICE_DIR / "service.json", encoding="utf-8") as handle:
        return json.load(handle)


def load_pack(version: str) -> dict[str, Any]:
    path = SERVICE_DIR / "versions" / version / "service_pack.json"
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_service_metadata_is_complete() -> None:
    service = load_service()
    assert service["slug"] == "delhi-income-certificate"
    assert service["geography"] == "Delhi"
    assert service["latest_version"] == "1.0.0"
    assert service["name"]
    assert service["department"]
    assert service["summary"]
    assert service["fee"]
    assert service["processing_time"]
    assert service["tags"]
    assert len(service["sources"]) >= 2
    for source in service["sources"]:
        assert source["title"]
        assert source["url"].startswith("https://")


def test_latest_pack_matches_metadata_version() -> None:
    service = load_service()
    pack = load_pack(service["latest_version"])
    assert pack["pack_version"] == service["latest_version"]
    assert pack["service_slug"] == service["slug"]


def test_pack_fields_use_known_bindings_and_formats() -> None:
    pack = load_pack("1.0.0")
    fields = pack["form_template"]["fields"]
    ids = [field["id"] for field in fields]
    assert len(ids) == len(set(ids))
    for field in fields:
        assert field["label"]
        if field["binding"] is not None:
            assert field["binding"] in FIELD_KEYS
        assert field["format"] in {"text", "numeric", "date", "aadhaar"}
        assert isinstance(field["required"], bool)
    assert any(field["required"] for field in fields)


def test_pack_checklist_groups_are_valid() -> None:
    pack = load_pack("1.0.0")
    groups = pack["checklist_groups"]
    group_ids = [group["id"] for group in groups]
    assert len(group_ids) == len(set(group_ids))
    for group in groups:
        assert group["label"]
        assert group["requirement"] in {"at_least_one", "optional"}
        assert isinstance(group["accepted_classifications"], list)
    assert any(group["requirement"] == "at_least_one" for group in groups)


def test_pack_declaration_and_guidance_are_present() -> None:
    pack = load_pack("1.0.0")
    assert pack["form_template"]["declaration"]["required"] is True
    assert pack["form_template"]["declaration"]["text"]
    assert pack["guidance"]["what_it_is"]
    assert len(pack["guidance"]["official_channel_steps"]) >= 1
    assert pack["guidance"]["not_a_submission_notice"]
