"""Document endpoints: streaming upload into a knowledge base."""

import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, UploadFile, status

from ragx.api.deps import SessionDep, SettingsDep, StorageDep, TenantContextDep
from ragx.api.schemas import DocumentResponse
from ragx.services.knowledge import upload_document

router = APIRouter(prefix="/v1/knowledge-bases", tags=["documents"])

_CHUNK_SIZE = 64 * 1024


async def _stream(file: UploadFile) -> AsyncIterator[bytes]:
    while chunk := await file.read(_CHUNK_SIZE):
        yield chunk


@router.post("/{kb_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload(
    kb_id: uuid.UUID,
    file: UploadFile,
    ctx: TenantContextDep,
    session: SessionDep,
    storage: StorageDep,
    settings: SettingsDep,
) -> DocumentResponse:
    document = await upload_document(
        session,
        ctx,
        storage,
        kb_id=kb_id,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        data=_stream(file),
        max_upload_bytes=settings.max_upload_size_mb * 1024 * 1024,
    )
    return DocumentResponse.model_validate(document)
