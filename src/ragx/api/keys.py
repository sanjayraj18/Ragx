"""API-key management endpoints: humans (JWT) mint keys for machines."""

from fastapi import APIRouter, status

from ragx.api.deps import CurrentUserDep, SessionDep, TenantContextDep
from ragx.api.schemas import ApiKeyCreateRequest, ApiKeyResponse
from ragx.services.identity import create_api_key, list_api_keys

router = APIRouter(prefix="/v1/api-keys",tags=["api-keys"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_key(body: ApiKeyCreateRequest, session : SessionDep, user : CurrentUserDep):
    ctx = TenantContextDep(tenant_id=user.tenant_id, user_id=user.id)
    api_key, plain_text = await create_api_key(session,ctx, name=body.name)
    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        is_active=api_key.is_active,
        api_key=plain_text,
    )

@router.get("")
async def list_keys(user: CurrentUserDep, session: SessionDep) -> list[ApiKeyResponse]:
    ctx = TenantContextDep(tenant_id=user.tenant_id, user_id=user.id)
    keys = await list_api_keys(session, ctx)
    return [ApiKeyResponse.model_validate(key) for key in keys]