import json
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from app.modules.documents.extraction import CLASSIFICATIONS

CATALOG_ROOT = Path(__file__).resolve().parents[4] / "catalog" / "services"

# A catalog version is a plain identifier such as "1.0.0". Anything with a
# separator or a parent reference must never be joined into a path.
_VERSION_PATTERN = re.compile(r"[0-9A-Za-z][0-9A-Za-z._-]*")


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class ServiceMetadata:
    slug: str
    name: str
    geography: str
    department: str
    latest_version: str
    summary: str
    tags: list[str]
    fee: str
    processing_time: str
    sources: list[dict[str, str]]


@dataclass(frozen=True)
class FormField:
    id: str
    label: str
    binding: str | None
    required: bool
    format: str


@dataclass(frozen=True)
class ChecklistGroup:
    id: str
    label: str
    requirement: str
    accepted_classifications: list[str]


@dataclass(frozen=True)
class ServicePack:
    pack_version: str
    service_slug: str
    guidance: dict[str, Any]
    checklist_groups: list[ChecklistGroup]
    fields: list[FormField]
    declaration: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"Invalid catalog file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CatalogError(f"Catalog file must contain an object: {path}")
    return data


def _find_service_dir(slug: str) -> Path | None:
    for path in CATALOG_ROOT.rglob("service.json"):
        if _read_json(path).get("slug") == slug:
            return path.parent
    return None


def _metadata(data: dict[str, Any]) -> ServiceMetadata:
    try:
        return ServiceMetadata(
            slug=data["slug"],
            name=data["name"],
            geography=data["geography"],
            department=data["department"],
            latest_version=data["latest_version"],
            summary=data["summary"],
            tags=data["tags"],
            fee=data["fee"],
            processing_time=data["processing_time"],
            sources=data["sources"],
        )
    except KeyError as exc:
        raise CatalogError(f"Service metadata missing key: {exc.args[0]}") from exc


def _checklist_group(data: dict[str, Any]) -> ChecklistGroup:
    group = ChecklistGroup(
        id=data["id"],
        label=data["label"],
        requirement=data["requirement"],
        accepted_classifications=data["accepted_classifications"],
    )
    # A pack is data edited outside the type checker, so a misspelt
    # classification must fail loudly: it either gates nothing or blocks the
    # group forever, and both look like a citizen's mistake at the UI.
    unknown = [
        name for name in group.accepted_classifications if name not in CLASSIFICATIONS
    ]
    if unknown:
        raise CatalogError(
            f"Checklist group {group.id} accepts unknown classifications: "
            f"{', '.join(map(str, unknown))}"
        )
    return group


def _pack(data: dict[str, Any]) -> ServicePack:
    try:
        template = data["form_template"]
        return ServicePack(
            pack_version=data["pack_version"],
            service_slug=data["service_slug"],
            guidance=data["guidance"],
            checklist_groups=[
                _checklist_group(group) for group in data["checklist_groups"]
            ],
            fields=[
                FormField(
                    id=field["id"],
                    label=field["label"],
                    binding=field["binding"],
                    required=field["required"],
                    format=field["format"],
                )
                for field in template["fields"]
            ],
            declaration=template["declaration"],
        )
    except KeyError as exc:
        raise CatalogError(f"Service pack missing key: {exc.args[0]}") from exc


@cache
def list_services() -> list[ServiceMetadata]:
    return [
        _metadata(_read_json(path))
        for path in sorted(CATALOG_ROOT.rglob("service.json"))
    ]


def get_service(slug: str) -> ServiceMetadata | None:
    return next((service for service in list_services() if service.slug == slug), None)


@cache
def get_pack(slug: str, version: str) -> ServicePack | None:
    directory = _find_service_dir(slug)
    if directory is None:
        return None
    # `version` comes from stored drafts and packet snapshots, so treat it as
    # untrusted: without this check a value containing "../" reads a sibling
    # service's pack (or any file named service_pack.json on disk).
    if not _VERSION_PATTERN.fullmatch(version):
        return None
    versions = (directory / "versions").resolve()
    path = (versions / version / "service_pack.json").resolve()
    if versions not in path.parents:
        return None
    if not path.exists():
        return None
    return _pack(_read_json(path))


def get_latest_pack(slug: str) -> ServicePack | None:
    service = get_service(slug)
    if service is None:
        return None
    return get_pack(slug, service.latest_version)
