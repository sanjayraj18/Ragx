"""Document endpoints: streaming upload into a knowledge base."""

from collections.abc import AsyncIterator
import uuid

from fastapi import APIRouter, File, Form, UploadFile, status

from ragx.api.deps import SessionDep, StorageDep, TenantContextDep
from ragx.api.schemas import DocumentResponse
from ragx.config import get_settings
from ragx.errors import UnsupportedMediaTypeError
from ragx.services.knowledge import upload_document

router = APIRouter(prefix="/v1/knowledge-bases", tags=["documents"])

_ALLOWED_CONTENT_TYPES = {"application/pdf", "text/plain", "text/markdown"}


@router.post("/{kb_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload(
      kb_id: uuid.UUID,
      ctx: TenantContextDep,
      session: SessionDep,
      storage: StorageDep,
      file: UploadFile = File(...),
  ) -> DocumentResponse:
      content_type = file.content_type or "application/octet-stream"
      if content_type not in _ALLOWED_CONTENT_TYPES:
          raise UnsupportedMediaTypeError(f"content type '{content_type}' is not accepted")

      settings = get_settings()
      document = await upload_document(
          session,
          ctx,
          storage,
          kb_id=kb_id,
          filename=file.filename or "unnamed",
          content_type=content_type,
          data=_stream(file),
          max_upload_bytes=settings.max_upload_size_mb * 1024 * 1024,
      )
      return DocumentResponse.model_validate(document)

async def _stream(file: UploadFile) -> "AsyncIterator[bytes]":
      while chunk := await file.read(64 * 1024):
        yield chunk