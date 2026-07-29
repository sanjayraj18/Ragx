"""FastAPI dependencies — the glue handing infrastructure to routes.

  get_session implements the unit-of-work contract: one fresh session per
  request; commit on success, rollback on failure, close always. Routes
  declare SessionDep and never think about transactions.
"""

from collections.abc import AsyncIterator
from typing import Annotated
import uuid

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ragx.config import Settings
from ragx.db.models.identity import User
from ragx.errors import UnauthorizedError
from ragx.security import decode_access_token


async def get_session(request : Request) -> AsyncIterator[AsyncSession]:
    factory : async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

SessionDep = Annotated[AsyncSession, Depends(get_session)]

def get_app_settings(request : Request) -> Settings:
    return request.app.state.settings

SettingsDep = Annotated[Settings, Depends(get_app_settings)]
_bearer = HTTPBearer(auto_error=False)

async def get_current_user(credentials : Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)], session :SessionDep, settings : SettingsDep) -> User:
    if credentials is None:
        raise UnauthorizedError("missing bearer token") 
    payload = decode_access_token(credentials,secret_key=settings.secret_key.get_secret_value())
    user = await session.get(User, uuid.UUID(payload["sub"]))

    if user is None or not user.is_active:
        raise UnauthorizedError("account not found or diabled")

    return user;

CurrentUserDep = Annotated[User, Depends(get_current_user)]