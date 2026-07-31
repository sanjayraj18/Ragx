"""Knowledge-base use-cases. Every function takes TenantContext: there is
no way to touch a KB except through a tenant scope. Cross-tenant access
is indistinguishable from nonexistence (404, never 403)."""

import uuid
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import uuid7

from ragx.context import TenantContext
from ragx.db.models import KnowledgeBase
from ragx.db.models.knowledge import Document
from ragx.errors import ConflictError, NotFoundError
from ragx.logging import get_logger
from ragx.storage.base import BlobStorage
from ragx.upload import UploadMeter

log = get_logger(__name__)


async def create_knowledge_base(
    session: AsyncSession, ctx: TenantContext, *, name: str, description: str = ""
) -> KnowledgeBase:
    duplicate = await session.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.tenant_id == ctx.tenant_id, KnowledgeBase.name == name
        )
    )
    if duplicate is not None:
        raise ConflictError(f"knowledge base '{name}' already exists")

    kb = KnowledgeBase(tenant_id=ctx.tenant_id, name=name, description=description)
    session.add(kb)
    await session.flush()
    log.info("knowledge_base_created", kb_id=str(kb.id))
    return kb


async def list_knowledge_bases(session: AsyncSession, ctx: TenantContext) -> list[KnowledgeBase]:
    result = await session.scalars(
        select(KnowledgeBase)
        .where(KnowledgeBase.tenant_id == ctx.tenant_id)
        .order_by(KnowledgeBase.created_at)
    )
    return list(result)


async def get_knowledge_base(
    session: AsyncSession, ctx: TenantContext, *, kb_id: uuid.UUID
) -> KnowledgeBase:
    kb = await session.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id, KnowledgeBase.tenant_id == ctx.tenant_id
        )
    )
    if kb is None:
        raise NotFoundError("knowledge base not found")
    return kb


async def delete_knowledge_base(
    session: AsyncSession, ctx: TenantContext, *, kb_id: uuid.UUID
) -> None:
    kb = await get_knowledge_base(session, ctx, kb_id=kb_id)
    await session.delete(kb)
    await session.flush()
    log.info("knowledge_base_deleted", kb_id=str(kb.id))


async def upload_document(
    session: AsyncSession,
    ctx: TenantContext,
    storage: BlobStorage,
    *,
    kb_id: uuid.UUID,
    filename: str,
    content_type: str,
    data: AsyncIterator[bytes],
    max_upload_bytes: int,
) -> Document:
    kb = await get_knowledge_base(session, ctx, kb_id=kb_id)

    document_id = uuid7()
    storage_key = f"tenants/{ctx.tenant_id}/documents/{document_id}"

    meter = UploadMeter(max_bytes=max_upload_bytes)
    await storage.store(storage_key, meter.measure(data))

    duplicate = await session.scalar(
        select(Document).where(
            Document.kb_id == kb.id,
            Document.content_hash == meter.content_hash,
        )
    )
    if duplicate is not None:
        await storage.delete(storage_key)
        raise ConflictError("this document already exists in the knowledge base")

    document = Document(
        id=document_id,
        kb_id=kb.id,
        filename=filename,
        content_type=content_type,
        size_bytes=meter.size,
        content_hash=meter.content_hash,
        storage_key=storage_key,
    )
    session.add(document)
    await session.flush()
    log.info(
        "document_uploaded",
        kb_id=str(kb.id),
        document_id=str(document.id),
        size_bytes=document.size_bytes,
    )
    return document
