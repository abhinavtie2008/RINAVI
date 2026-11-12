import uuid

from fastapi import APIRouter, HTTPException, Response, UploadFile, status

from app.api.deps import ConsentRequired, CurrentUser, DbSession
from app.modules.audit.service import emit_audit
from app.modules.documents.pipeline import process_document
from app.modules.vault import schemas, service, validation
from app.modules.vault.models import DocumentStatus
from app.modules.vault.storage import get_storage

router = APIRouter(prefix="/vault", tags=["vault"])


@router.post(
    "/documents",
    response_model=schemas.DocumentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ConsentRequired("documents.processing")],
)
async def upload_document(
    file: UploadFile, user: CurrentUser, db: DbSession
) -> schemas.DocumentOut:
    data = await file.read(validation.MAX_UPLOAD_BYTES + 1)
    if len(data) > validation.MAX_UPLOAD_BYTES:
        # Numeric 413: the Starlette constant name changed across versions.
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB limit")
    content_type = validation.sniff_content_type(data)
    if content_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Supported types: PDF, PNG, JPEG, TXT",
        )

    document = await service.create_document(
        db,
        get_storage(),
        user,
        filename=file.filename or "document",
        content_type=content_type,
        data=data,
    )
    await process_document(db, get_storage(), document)
    await emit_audit(
        db,
        actor_user_id=user.id,
        action="document.uploaded",
        resource_type="document",
        resource_id=str(document.id),
        details={"content_type": content_type, "size_bytes": len(data)},
    )
    if document.status == DocumentStatus.PROCESSED:
        await emit_audit(
            db,
            actor_user_id=user.id,
            action="document.processed",
            resource_type="document",
            resource_id=str(document.id),
            details={"classification": document.classification},
        )
    await db.commit()
    return schemas.DocumentOut.model_validate(document)


@router.get(
    "/documents",
    response_model=list[schemas.DocumentOut],
    dependencies=[ConsentRequired("documents.processing")],
)
async def list_my_documents(
    user: CurrentUser, db: DbSession
) -> list[schemas.DocumentOut]:
    documents = await service.list_documents(db, user)
    return [schemas.DocumentOut.model_validate(d) for d in documents]


@router.get(
    "/documents/{document_id}",
    response_model=schemas.DocumentOut,
    dependencies=[ConsentRequired("documents.processing")],
)
async def get_document(
    document_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> schemas.DocumentOut:
    document = await service.get_own_document(db, user, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return schemas.DocumentOut.model_validate(document)


@router.get(
    "/documents/{document_id}/content",
    dependencies=[ConsentRequired("documents.processing")],
)
async def document_content(
    document_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> Response:
    document = await service.get_own_document(db, user, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    data = get_storage().read(user.id, document.id)
    return Response(content=data, media_type=document.content_type)


@router.get(
    "/documents/{document_id}/fields",
    response_model=list[schemas.ExtractedFieldOut],
    dependencies=[ConsentRequired("documents.processing")],
)
async def document_fields(
    document_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> list[schemas.ExtractedFieldOut]:
    document = await service.get_own_document(db, user, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    fields = await service.list_fields(db, document)
    return [schemas.ExtractedFieldOut.model_validate(f) for f in fields]


@router.post(
    "/documents/{document_id}/retry",
    response_model=schemas.DocumentOut,
    dependencies=[ConsentRequired("documents.processing")],
)
async def retry_document(
    document_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> schemas.DocumentOut:
    document = await service.get_own_document(db, user, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await process_document(db, get_storage(), document)
    if document.status == DocumentStatus.PROCESSED:
        await emit_audit(
            db,
            actor_user_id=user.id,
            action="document.processed",
            resource_type="document",
            resource_id=str(document.id),
            details={"classification": document.classification, "retry": True},
        )
    await db.commit()
    return schemas.DocumentOut.model_validate(document)
