"""The consumer-facing retrieval endpoint — the contract programs call.

Scores order results within one response; they are not comparable across
modes or requests. Provenance (filename, pages) is included so a result
is citable and fetchable without follow-up calls."""

from fastapi import APIRouter

from ragx.api.deps import SessionDep, SettingsDep, TenantContextDep
from ragx.api.schemas import RetrievalRequest, RetrievalResponse, RetrievalResult
from ragx.services.retrieval import retrieve

router = APIRouter(prefix="/v1/retrieval", tags=["retrieval"])


@router.post("")
async def retrieval(
    body: RetrievalRequest,
    ctx: TenantContextDep,
    session: SessionDep,
    settings: SettingsDep,
) -> RetrievalResponse:
    """Retrieve the k most relevant chunks from a knowledge base.

    `score` is mode-relative: it orders results within this response and
    must not be compared across modes or requests. `rerank=true` improves
    precision at the cost of added latency (see `took_ms`).
    """
    outcome = await retrieve(
        session,
        ctx,
        settings,
        kb_id=body.kb_id,
        query=body.query,
        k=body.k,
        mode=body.mode,
        rerank=body.rerank,
    )
    return RetrievalResponse(
        results=[
            RetrievalResult(
                chunk_id=r.chunk.id,
                document_id=r.document.id,
                filename=r.document.filename,
                content_type=r.document.content_type,
                position=r.chunk.position,
                text=r.chunk.text,
                page_start=r.chunk.page_start,
                page_end=r.chunk.page_end,
                score=r.score,
            )
            for r in outcome.results
        ],
        query=body.query,
        mode=body.mode,
        reranked=body.rerank,
        took_ms=outcome.took_ms,
    )
