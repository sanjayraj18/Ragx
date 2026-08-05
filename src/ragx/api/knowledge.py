"""Knowledge-base endpoints — the first full tenant-data resource."""

import uuid

from fastapi import APIRouter, status

from ragx.api.deps import SessionDep, SettingsDep, TenantContextDep
from ragx.api.schemas import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseResponse,
    SearchRequest,
    SearchResult,
)
from ragx.services.knowledge import (
    create_knowledge_base,
    delete_knowledge_base,
    get_knowledge_base,
    list_knowledge_bases,
    vector_search_chunks,
)

router = APIRouter(prefix="/v1/knowledge-bases", tags=["knowledge-bases"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_kb(
    body: KnowledgeBaseCreateRequest,
    ctx: TenantContextDep,
    session: SessionDep,
    settings: SettingsDep,
) -> KnowledgeBaseResponse:
    kb = await create_knowledge_base(
        session,
        ctx,
        settings,
        name=body.name,
        description=body.description,
        embedding_model=body.embedding_model,
    )
    return KnowledgeBaseResponse.model_validate(kb)


@router.get("")
async def list_kbs(ctx: TenantContextDep, session: SessionDep) -> list[KnowledgeBaseResponse]:
    kbs = await list_knowledge_bases(session, ctx)
    return [KnowledgeBaseResponse.model_validate(kb) for kb in kbs]


@router.get("/{kb_id}")
async def get_kb(
    kb_id: uuid.UUID, ctx: TenantContextDep, session: SessionDep
) -> KnowledgeBaseResponse:
    kb = await get_knowledge_base(session, ctx, kb_id=kb_id)
    return KnowledgeBaseResponse.model_validate(kb)


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb(kb_id: uuid.UUID, ctx: TenantContextDep, session: SessionDep) -> None:
    await delete_knowledge_base(session, ctx, kb_id=kb_id)

@router.post("/{kb_id}/search")
async def search_kb(
      kb_id: uuid.UUID,
      body: SearchRequest,
      ctx: TenantContextDep,
      session: SessionDep,
      settings: SettingsDep,
  ) -> list[SearchResult]:
      results = await vector_search_chunks(
          session, ctx, settings, kb_id=kb_id, query=body.query, limit=body.limit
      )
      return [
          SearchResult(
              chunk_id=chunk.id,
              document_id=chunk.document_id,
              position=chunk.position,
              text=chunk.text,
              page_start=chunk.page_start,
              page_end=chunk.page_end,
              score=1.0 - distance,
          )
          for chunk, distance in results
      ]
