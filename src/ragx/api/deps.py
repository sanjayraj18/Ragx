"""FastAPI dependencies — the glue handing infrastructure to routes.

  get_session implements the unit-of-work contract: one fresh session per
  request; commit on success, rollback on failure, close always. Routes
  declare SessionDep and never think about transactions.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


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
