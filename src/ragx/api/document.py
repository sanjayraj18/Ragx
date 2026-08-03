"""Document endpoints: streaming upload/download, listing, and deletion.

The list lives under its knowledge base (containment is real there); item
operations live at a flat /v1/documents path — an ID needs no parent.
Blob deletion runs as a background task, after the row's death commits."""

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, UploadFile, background, status
from fastapi.responses import StreamingResponse

from ragx.api.deps import SessionDep, SettingsDep, StorageDep, TenantContextDep
from ragx.api.schemas import DocumentResponse
from ragx.services.knowledge import (
    delete_document,
    get_document,
    list_documents,
    upload_document,
)

router = APIRouter(prefix="/v1/knowledge-bases", tags=["documents"])
item_router = APIRouter(prefix="/v1/documents", tags=["documents"])

_CHUNK_SIZE = 64 * 1024


async def _stream(file: UploadFile) -> AsyncIterator[bytes]:
    while chunk := await file.read(_CHUNK_SIZE):
        yield chunk

def _enqueue_ingest(document_id : str) ->None:
    from ragx.worker.celery_app import celery_app
    celery_app.send_task("ragx.worker.tasks.ingest_document", args=[document_id])


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
    background.add_task(_enqueue_ingest, str(document.id))
    return DocumentResponse.model_validate(document)


@router.get("/{kb_id}/documents")
async def list_docs(
    kb_id: uuid.UUID,
    ctx: TenantContextDep,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DocumentResponse]:
    documents = await list_documents(session, ctx, kb_id=kb_id, limit=limit, offset=offset)
    return [DocumentResponse.model_validate(d) for d in documents]


@item_router.get("/{document_id}")
async def get_doc(
    document_id: uuid.UUID, ctx: TenantContextDep, session: SessionDep
) -> DocumentResponse:
    document = await get_document(session, ctx, document_id=document_id)
    return DocumentResponse.model_validate(document)


@item_router.get("/{document_id}/download")
async def download_doc(
    document_id: uuid.UUID,
    ctx: TenantContextDep,
    session: SessionDep,
    storage: StorageDep,
) -> StreamingResponse:
    document = await get_document(session, ctx, document_id=document_id)
    filename = document.filename.replace('"', "")
    return StreamingResponse(
        storage.retrieve(document.storage_key),
        media_type=document.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(document.size_bytes),
        },
    )


@item_router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doc(
    document_id: uuid.UUID,
    ctx: TenantContextDep,
    session: SessionDep,
    storage: StorageDep,
    background: BackgroundTasks,
) -> None:
    storage_key = await delete_document(session, ctx, document_id=document_id)
    background.add_task(storage.delete, storage_key)
