"""FastAPI dependencies — the glue handing infrastructure to routes.

get_session implements the unit-of-work contract: one fresh session per
request; commit on success, rollback on failure, close always. Routes
declare SessionDep and never think about transactions.
"""

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

import structlog
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ragx.config import Settings
from ragx.context import TenantContext
from ragx.db.models.identity import User
from ragx.errors import UnauthorizedError
from ragx.security import decode_access_token
from ragx.services.identity import authenticate_api_key


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: SessionDep,
    settings: SettingsDep,
) -> User:
    if credentials is None:
        raise UnauthorizedError("missing bearer token")
    payload = decode_access_token(
        credentials.credentials, secret_key=settings.secret_key.get_secret_value()
    )
    user = await session.get(User, uuid.UUID(payload["sub"]))

    if user is None or not user.is_active:
        raise UnauthorizedError("account not found or diabled")

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_tenant_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: SessionDep,
    settings: SettingsDep,
) -> TenantContext:
    if credentials is None:
        raise UnauthorizedError("missing credentials")
    token = credentials.credentials

    if token.startswith("ragx_"):
        api_key = await authenticate_api_key(session=session, key=token)
        ctx = TenantContext(tenant_id=api_key.tenant_id, api_key_id=api_key.id)
    else:
        payload = decode_access_token(
            token=token, secret_key=settings.secret_key.get_secret_value()
        )
        user = await session.get(User, uuid.UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise UnauthorizedError("account not found or disabled")
        ctx = TenantContext(tenant_id=user.tenant_id, user_id=user.id)

    structlog.contextvars.bind_contextvars(tenant_id=str(ctx.tenant_id))
    return ctx


TenantContextDep = Annotated[TenantContext, Depends(get_tenant_context)]
