

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ragx.logging import get_logger
from ragx.db.models.identity import Tenant, User
from ragx.errors import ConflictError
from ragx.security import hashPassword

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

    
