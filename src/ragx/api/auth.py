"""Authentication endpoints: the HTTP skin over identity services."""

from fastapi import APIRouter,status

from ragx.api.deps import SessionDep
from ragx.api.schemas import RegisterRequest, UserResponse
from ragx.services.identity import register_tenant

router = APIRouter(prefix="/v1/auth",tags=["auth"])

@router.post("/register",status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, session:SessionDep) -> UserResponse:
    user = await register_tenant(session,tenant_name=body.tenant_name,email=body.email,password=body.password);
    return UserResponse.model_validate(user)
