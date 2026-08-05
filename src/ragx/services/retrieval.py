"""Retrieval: the composed funnel behind the consumer-facing endpoint.

Composes the search stages (dense / lexical / fused, optional rerank) and
joins document provenance in one batch query — a result must be usable
without follow-up requests."""

import time
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ragx.config import Settings
from ragx.context import TenantContext
from ragx.db.models import Chunk, Document
from ragx.services.knowledge import (
    CANDIDATE_POOL,
    hybrid_search_chunks,
    keyword_search_chunks,
    rerank_chunks,
    vector_search_chunks,
)


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk: Chunk
    document: Document
    score: float


@dataclass(frozen=True, slots=True)
class RetrievalOutcome:
    results: list[RetrievedChunk]
    took_ms: int


async def retrieve(
    session: AsyncSession,
    ctx: TenantContext,
    settings: Settings,
    *,
    kb_id: uuid.UUID,
    query: str,
    k: int,
    mode: str,
    rerank: bool,
) -> RetrievalOutcome:
    started = time.perf_counter()
    fetch_limit = CANDIDATE_POOL if rerank else k

    if mode == "vector":
        scored = await vector_search_chunks(
            session, ctx, settings, kb_id=kb_id, query=query, limit=fetch_limit
        )
    elif mode == "keyword":
        scored = await keyword_search_chunks(
            session, ctx, kb_id=kb_id, query=query, limit=fetch_limit
        )
    else:
        scored = await hybrid_search_chunks(
            session, ctx, settings, kb_id=kb_id, query=query, limit=fetch_limit
        )

    if rerank:
        scored = await rerank_chunks(settings, query=query, candidates=scored, limit=k)

    document_ids = {chunk.document_id for chunk, _ in scored}
    documents = (
        {
            d.id: d
            for d in await session.scalars(select(Document).where(Document.id.in_(document_ids)))
        }
        if document_ids
        else {}
    )

    results = [
        RetrievedChunk(chunk=chunk, document=documents[chunk.document_id], score=score)
        for chunk, score in scored
    ]
    took_ms = int((time.perf_counter() - started) * 1000)
    return RetrievalOutcome(results=results, took_ms=took_ms)
