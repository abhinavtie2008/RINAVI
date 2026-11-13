from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.modules.catalog import loader, schemas

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _summary(service: loader.ServiceMetadata) -> schemas.ServiceSummaryOut:
    return schemas.ServiceSummaryOut(
        slug=service.slug,
        name=service.name,
        geography=service.geography,
        department=service.department,
        latest_version=service.latest_version,
        summary=service.summary,
        fee=service.fee,
        processing_time=service.processing_time,
    )


@router.get("/services", response_model=list[schemas.ServiceSummaryOut])
async def list_services(_: CurrentUser) -> list[schemas.ServiceSummaryOut]:
    return [_summary(service) for service in loader.list_services()]


@router.get("/services/{slug}", response_model=schemas.ServiceDetailOut)
async def get_service(slug: str, _: CurrentUser) -> schemas.ServiceDetailOut:
    service = loader.get_service(slug)
    pack = loader.get_latest_pack(slug)
    if service is None or pack is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    return schemas.ServiceDetailOut(
        **_summary(service).model_dump(),
        tags=service.tags,
        sources=[schemas.CatalogSourceOut(**source) for source in service.sources],
        guidance=pack.guidance,
        checklist_groups=[
            schemas.ChecklistGroupOut(
                id=group.id,
                label=group.label,
                requirement=group.requirement,
                accepted_classifications=group.accepted_classifications,
            )
            for group in pack.checklist_groups
        ],
        fields=[
            schemas.CatalogFieldOut(
                id=field.id,
                label=field.label,
                binding=field.binding,
                required=field.required,
                format=field.format,
            )
            for field in pack.fields
        ],
        declaration=pack.declaration,
    )
