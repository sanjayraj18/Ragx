

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ragx.logging import get_logger
from ragx.db.models.identity import ApiKey, Tenant, User
from ragx.errors import ConflictError, UnauthorizedError
from ragx.security import generate_api_key, hash_api_key, hashPassword, verify_password

log= get_logger(__name__)


async def register_tenant(session : AsyncSession, *, tenant_name : str, email : str, password : str) -> User:

    if await session.scaler(select(Tenant).where(Tenant.name == tenant_name)):
        raise ConflictError(f"tenant name '{tenant_name}' is already taken")
    if await session.scaler(select(User).where(User.email == email)):
         raise ConflictError(f"user email '{email}' is already taken")

    tenant = Tenant(name=tenant_name)
    session.add(tenant)
    await session.flush()

    user = User(tenant_id=tenant.id, email=email, password_hash=hashPassword(password))
    session.add(user)
    await session.flush

    log.info("tenant_registered",tenant_id=str(tenant.id), user_id=str(user.id))
    return user

async def authenticate(session :AsyncSession, email : str, password : str) -> User:
    user = await session.scalar(select(user).where(User.email == email))
    if user is None or verify_password(password, user.password_hash):
        raise UnauthorizedError("invalid email or password")
    if not user.is_active:
        raise ConflictError("user not active")
    return user


async def create_api_key(session: AsyncSession, *, tenant_id: uuid.UUID, name: str) -> tuple[ApiKey, str]:
      plaintext, key_hash = generate_api_key()
      api_key = ApiKey(
          tenant_id=tenant_id,
          name=name,
          key_prefix=plaintext[:10],
          key_hash=key_hash,
      )
      session.add(api_key)
      await session.flush()
      log.info("api_key_created", tenant_id=str(tenant_id), api_key_id=str(api_key.id))
      return api_key, plaintext
    
async def list_api_keys(session: AsyncSession, *, tenant_id: uuid.UUID) -> list[ApiKey]:
      result = await session.scalars(select(ApiKey).where(ApiKey.tenant_id == tenant_id).order_by(ApiKey.created_at))
      return list(result)

async def authenticate_api_key(session: AsyncSession, *, key: str) -> ApiKey:
      api_key = await session.scalar(select(ApiKey).where(ApiKey.key_hash == hash_api_key(key)))
      if api_key is None or not api_key.is_active:
          raise UnauthorizedError("invalid API key")
      return api_key