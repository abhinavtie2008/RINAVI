import json
from pathlib import Path

import pytest

from app.modules.catalog import loader
from app.modules.catalog.loader import CatalogError


def test_list_services_finds_delhi_income_certificate() -> None:
    services = loader.list_services()
    assert {service.slug for service in services} >= {"delhi-income-certificate"}
    service = next(s for s in services if s.slug == "delhi-income-certificate")
    assert service.geography == "Delhi"
    assert service.latest_version == "1.0.0"


def test_get_latest_pack_parses_fields_and_groups() -> None:
    pack = loader.get_latest_pack("delhi-income-certificate")
    assert pack is not None
    assert pack.pack_version == "1.0.0"
    field_ids = [field.id for field in pack.fields]
    assert "applicant_name" in field_ids
    assert "purpose" in field_ids
    applicant = next(f for f in pack.fields if f.id == "applicant_name")
    assert applicant.binding == "full_name"
    assert applicant.required is True
    groups = {group.id: group for group in pack.checklist_groups}
    assert groups["income_evidence"].requirement == "at_least_one"
    assert groups["income_evidence"].accepted_classifications == ["income"]
    assert pack.declaration["required"] is True


def test_unknown_service_and_version_return_none() -> None:
    assert loader.get_service("no-such-service") is None
    assert loader.get_latest_pack("no-such-service") is None
    assert loader.get_pack("delhi-income-certificate", "0.0.1") is None


def test_corrupt_pack_raises_catalog_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service_dir = tmp_path / "edistrict" / "income-certificate"
    (service_dir / "versions" / "1.0.0").mkdir(parents=True)
    (service_dir / "service.json").write_text(
        '{"slug": "delhi-income-certificate", "latest_version": "1.0.0"}',
        encoding="utf-8",
    )
    (service_dir / "versions" / "1.0.0" / "service_pack.json").write_text(
        "{this is not json", encoding="utf-8"
    )
    monkeypatch.setattr(loader, "CATALOG_ROOT", tmp_path)
    loader.list_services.cache_clear()
    loader.get_pack.cache_clear()
    with pytest.raises(CatalogError):
        loader.get_pack("delhi-income-certificate", "1.0.0")


def _write_service(root: Path, slug: str) -> Path:
    service_dir = root / "edistrict" / slug
    version_dir = service_dir / "versions" / "1.0.0"
    version_dir.mkdir(parents=True)
    (service_dir / "service.json").write_text(
        json.dumps({"slug": slug, "latest_version": "1.0.0"}), encoding="utf-8"
    )
    (version_dir / "service_pack.json").write_text(
        json.dumps(
            {
                "pack_version": "1.0.0",
                "service_slug": slug,
                "guidance": {},
                "checklist_groups": [],
                "form_template": {"fields": [], "declaration": {}},
            }
        ),
        encoding="utf-8",
    )
    return service_dir


def test_version_cannot_read_another_services_pack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # `version` is stored in drafts and packet snapshots, so it is untrusted.
    # Joined straight into a path, a separator walks out of this service's
    # directory and reads a sibling service's pack.
    _write_service(tmp_path, "own-service")
    _write_service(tmp_path, "other-service")
    monkeypatch.setattr(loader, "CATALOG_ROOT", tmp_path)
    loader.list_services.cache_clear()
    loader.get_pack.cache_clear()

    escaped = loader.get_pack("own-service", "../../other-service/versions/1.0.0")

    assert escaped is None


def test_pack_naming_an_unknown_classification_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A misspelt classification gates nothing (no document matches it) or
    # blocks the group forever, and either way the failure is silent.
    service_dir = _write_service(tmp_path, "own-service")
    pack_path = service_dir / "versions" / "1.0.0" / "service_pack.json"
    data = json.loads(pack_path.read_text(encoding="utf-8"))
    data["checklist_groups"] = [
        {
            "id": "residence_proof",
            "label": "Residence proof",
            "requirement": "at_least_one",
            "accepted_classifications": ["residance"],
        }
    ]
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(loader, "CATALOG_ROOT", tmp_path)
    loader.list_services.cache_clear()
    loader.get_pack.cache_clear()

    with pytest.raises(CatalogError, match="residance"):
        loader.get_pack("own-service", "1.0.0")


def test_pack_naming_an_unknown_requirement_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The validator treats every value other than "at_least_one" as optional,
    # so a misspelt requirement would switch a mandatory group off silently.
    service_dir = _write_service(tmp_path, "own-service")
    pack_path = service_dir / "versions" / "1.0.0" / "service_pack.json"
    data = json.loads(pack_path.read_text(encoding="utf-8"))
    data["checklist_groups"] = [
        {
            "id": "residence_proof",
            "label": "Residence proof",
            "requirement": "atleast_one",
            "accepted_classifications": ["residence"],
        }
    ]
    pack_path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(loader, "CATALOG_ROOT", tmp_path)
    loader.list_services.cache_clear()
    loader.get_pack.cache_clear()

    with pytest.raises(CatalogError, match="atleast_one"):
        loader.get_pack("own-service", "1.0.0")
