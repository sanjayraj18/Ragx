"""Knowledge-base use-cases. Every function takes TenantContext: there is
  no way to touch a KB except through a tenant scope. Cross-tenant access
  is indistinguishable from nonexistence (404, never 403)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ragx.context import TenantContext
from ragx.errors import ConflictError, NotFoundError
from ragx.logging import get_logger
from ragx.db.models import KnowledgeBase

log = get_logger(__name__)

async def create_knowledge_base(session: AsyncSession, ctx: TenantContext, *, name: str, description: str = "") -> KnowledgeBase:
    duplicate = await session.scalar(select(KnowledgeBase).where(KnowledgeBase.tenant_id == ctx.tenant_id, KnowledgeBase.name == name))
    if duplicate is not None:
        raise ConflictError(f"knowledge base '{name}' already exists")

    kb = KnowledgeBase(tenant_id= ctx.tenant_id, name=name, description=description)
    session.add(kb)
    await session.flush()
    log.info("knowledge_base_created", kb_id=str(kb.id))
    return kb

async def list_knowledge_bases(
      session: AsyncSession, ctx: TenantContext
  ) -> list[KnowledgeBase]:
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