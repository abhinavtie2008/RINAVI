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
