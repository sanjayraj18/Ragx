"""Knowledge-base use-cases. Every function takes TenantContext: there is
no way to touch a KB except through a tenant scope. Cross-tenant access
is indistinguishable from nonexistence (404, never 403)."""

import uuid
from collections.abc import AsyncIterator
from pathlib import PurePosixPath

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import uuid7

from ragx.config import Settings
from ragx.context import TenantContext
from ragx.db.models import KnowledgeBase
from ragx.db.models.knowledge import Chunk, Document, DocumentStatus
from ragx.embeddings import EMBEDDING_DIMENSION, provider_for
from ragx.errors import ConflictError, NotFoundError, UnsupportedMediaTypeError
from ragx.logging import get_logger
from ragx.parsing import PARSERS
from ragx.storage.base import BlobStorage
from ragx.upload import UploadMeter

log = get_logger(__name__)

ALLOWED_CONTENT_TYPES = frozenset(PARSERS)


async def create_knowledge_base(
    session: AsyncSession,
    ctx: TenantContext,
    settings: Settings,
    *,
    name: str,
    description: str = "",
    embedding_model: str = "openai/text-embedding-3-small",
) -> KnowledgeBase:
    provider = provider_for(embedding_model, settings)
    if provider.dimension != EMBEDDING_DIMENSION:
        raise ConflictError(
            f"model '{embedding_model}' produces {provider.dimension}-dim vectors; "
            f"this deployment stores {EMBEDDING_DIMENSION}"
        )

    duplicate = await session.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.tenant_id == ctx.tenant_id, KnowledgeBase.name == name
        )
    )
    if duplicate is not None:
        raise ConflictError(f"knowledge base '{name}' already exists")

    kb = KnowledgeBase(
        tenant_id=ctx.tenant_id,
        name=name,
        description=description,
        embedding_model=embedding_model,
    )
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
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedMediaTypeError(f"content type '{content_type}' is not accepted")

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
        tenant_id=ctx.tenant_id,
        kb_id=kb.id,
        filename=PurePosixPath(filename).name or "upload",
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


async def list_documents(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    kb_id: uuid.UUID,
    limit: int,
    offset: int,
) -> list[Document]:
    await get_knowledge_base(session, ctx, kb_id=kb_id)
    result = await session.scalars(
        select(Document)
        .where(Document.kb_id == kb_id, Document.tenant_id == ctx.tenant_id)
        .order_by(Document.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result)


async def get_document(
    session: AsyncSession, ctx: TenantContext, *, document_id: uuid.UUID
) -> Document:
    document = await session.scalar(
        select(Document).where(Document.id == document_id, Document.tenant_id == ctx.tenant_id)
    )
    if document is None:
        raise NotFoundError("document not found")
    return document


async def delete_document(
    session: AsyncSession, ctx: TenantContext, *, document_id: uuid.UUID
) -> str:
    document = await get_document(session, ctx, document_id=document_id)
    storage_key = document.storage_key
    await session.delete(document)
    await session.flush()
    log.info("document_deleted", document_id=str(document_id))
    return storage_key


async def list_chunks(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    document_id: uuid.UUID,
    limit: int,
    offset: int,
) -> list[Chunk]:
    await get_document(session, ctx, document_id=document_id)  # ownership check
    result = await session.scalars(
        select(Chunk)
        .where(Chunk.document_id == document_id, Chunk.tenant_id == ctx.tenant_id)
        .order_by(Chunk.position)
        .limit(limit)
        .offset(offset)
    )
    return list(result)


async def request_reingest(
    session: AsyncSession, ctx: TenantContext, *, document_id: uuid.UUID
) -> Document:
    document = await get_document(session, ctx, document_id=document_id)  # ownership check
    if document.status is DocumentStatus.PARSING:
        raise ConflictError("ingestion is already in progress")  # the guard → 409
    document.status = DocumentStatus.PENDING
    document.error_message = None
    await session.flush()
    return document

async def search_chunks(session : AsyncSession, ctx : TenantContext, settings : Settings, *, kb_id : uuid.UUID, query:str, limit : int) -> list[tuple[Chunk, float]]:
    kb = await get_knowledge_base(session, ctx, kb_id=kb_id)
    provider = provider_for(kb.embedding_model, settings)
    query_vector = (await provider.embed_batch([query]))[0]

    distance = Chunk.embedding.cosine_distance(query_vector)
    result = await session.execute(
        select(Chunk, distance.label("distance")).where(
            Chunk.kb_id == kb.id,
            Chunk.tenant_id == ctx.tenant_id,
            Chunk.embedding.is_not(None)
        ).order_by(distance).limit(limit)
    )

    return [(chunk, dist) for chunk, dist in result.all()]