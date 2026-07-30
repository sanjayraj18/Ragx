"""Tenant endpoints: what the authenticated scope can see about itself."""

from fastapi import APIRouter

from ragx.api.deps import SessionDep, TenantContextDep
from ragx.api.schemas import TenantResponse
from ragx.db.models import Tenant

router = APIRouter(prefix="/v1/tenant", tags=["tenant"])


@router.get("")
async def tenant_info(ctx: TenantContextDep, session: SessionDep) -> TenantResponse:
    tenant = await session.get(Tenant, ctx.tenant_id)
    assert tenant is not None
    return TenantResponse.model_validate(tenant)
