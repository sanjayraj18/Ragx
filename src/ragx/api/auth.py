"""Authentication endpoints: the HTTP skin over identity services."""

from fastapi import APIRouter,status

from ragx.api.deps import CurrentUserDep, SessionDep, SettingsDep
from ragx.api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from ragx.security import create_access_token
from ragx.services.identity import authenticate, register_tenant

router = APIRouter(prefix="/v1/auth",tags=["auth"])

@router.post("/register",status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, session:SessionDep) -> UserResponse:
    user = await register_tenant(session,tenant_name=body.tenant_name,email=body.email,password=body.password);
    return UserResponse.model_validate(user)

@router.post("/login", status_code=status.HTTP_201_CREATED)
async def login(body : LoginRequest, session : SessionDep, settings : SettingsDep) -> TokenResponse:
    user = await authenticate(session=session,email=body.email, password=body.password)
    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id,secret_key=settings.secret_key.get_secret_value(), expires_minutes=settings.access_token_expire_minutes)

    return TokenResponse(access_token=token)
    
@router.get("/me")
async def me(user : CurrentUserDep) -> UserResponse:
    return UserResponse.model_validate(user)