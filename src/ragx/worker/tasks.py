"""The ingestion task: blob → parse → chunk → rows, walking the status
machine. Idempotent by delete-and-reinsert: an at-least-once redelivery
converges instead of duplicating. Transient errors retry with backoff;
parse errors go straight to FAILED — retrying a corrupt PDF re-fails."""

import asyncio
import uuid

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncEngine

from ragx.chunking import default_chunker
from ragx.config import get_settings
from ragx.db.models.knowledge import Chunk, Document, DocumentStatus, KnowledgeBase
from ragx.db.session import create_engine, create_session_factory
from ragx.embeddings import EMBEDDING_DIMENSION, provider_for
from ragx.logging import configure_logging, get_logger
from ragx.parsing import parser_for
from ragx.storage.local import LocalStorage
from ragx.worker.celery_app import celery_app

log = get_logger(__name__)

_engine: AsyncEngine | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        configure_logging(get_settings())
        _engine = create_engine(get_settings())
    return _engine


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    autoretry_for=(ConnectionError, OSError),
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=3,
)
def ingest_document(self, document_id: str) -> None:  # type: ignore[no-untyped-def]
    asyncio.run(_ingest(uuid.UUID(document_id)))


async def _ingest(document_id: uuid.UUID) -> None:
    settings = get_settings()
    storage = LocalStorage(root=settings.storage_root)
    factory = create_session_factory(_get_engine())

    async with factory() as session:
        document = await session.scalar(select(Document).where(Document.id == document_id))
        if document is None:
            log.warning("ingest_document_missing", document_id=str(document_id))
            return
        kb = await session.scalar(select(KnowledgeBase).where(KnowledgeBase.id == document.kb_id))
        assert kb is not None  # FK guarantees it

        document.status = DocumentStatus.PARSING
        document.error_message = None
        await session.commit()

        try:
            data = b"".join([c async for c in storage.retrieve(document.storage_key)])
            parsed = parser_for(document.content_type).parse(data)
            drafts = default_chunker().chunk(
                parsed, chunk_size=kb.chunk_size, chunk_overlap=kb.chunk_overlap
            )

            await session.execute(delete(Chunk).where(Chunk.document_id == document_id))
            session.add_all(
                Chunk(
                    tenant_id=document.tenant_id,
                    kb_id=document.kb_id,
                    document_id=document.id,
                    position=d.position,
                    text=d.text,
                    page_start=d.page_start,
                    page_end=d.page_end,
                )
                for d in drafts
            )
            document.status = DocumentStatus.CHUNKED
            await session.commit()
            log.info("document_chunked", document_id=str(document.id), chunks=len(drafts))

            await _embed_pending(session, document, kb.embedding_model)
        except (ConnectionError, OSError, httpx.TimeoutException, httpx.TransportError):
            raise  # transient — Celery retries; NULL-bookkeeping makes the retry cheap
        except Exception as exc:
            await session.rollback()
            document.status = DocumentStatus.FAILED
            document.error_message = str(exc)[:2000]
            await session.commit()
            log.error("document_ingest_failed", document_id=str(document.id), error=str(exc))


_EMBED_BATCH = 64


async def _embed_pending(  # type: ignore[no-untyped-def]
    session, document, embedding_model: str
) -> None:
    settings = get_settings()
    provider = provider_for(embedding_model, settings)
    if provider.dimension != EMBEDDING_DIMENSION:
        raise ValueError(
            f"model '{embedding_model}' produces {provider.dimension}-dim vectors; "
            f"column stores {EMBEDDING_DIMENSION}"
        )

    document.status = DocumentStatus.EMBEDDING
    await session.commit()

    embedded_total = 0
    while True:
        pending = list(
            await session.scalars(
                select(Chunk)
                .where(Chunk.document_id == document.id, Chunk.embedding.is_(None))
                .order_by(Chunk.position)
                .limit(_EMBED_BATCH)
            )
        )
        if not pending:
            break
        vectors = await provider.embed_batch([c.text for c in pending])
        for chunk, vector in zip(pending, vectors, strict=True):
            chunk.embedding = vector
        await session.commit()  # ← the checkpoint: this batch is safe forever
        embedded_total += len(pending)
        log.info(
            "chunks_embedded",
            document_id=str(document.id),
            batch=len(pending),
            total=embedded_total,
        )

    document.status = DocumentStatus.READY
    await session.commit()
    log.info("document_ready", document_id=str(document.id))
