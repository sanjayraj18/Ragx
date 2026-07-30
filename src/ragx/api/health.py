"""Liveness and readiness probes — different questions, different endpoints."""

from fastapi import APIRouter, Response
from sqlalchemy import text

from ragx.api.deps import SessionDep

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness: is the process running? Restart me if this fails."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(session: SessionDep, response: Response) -> dict[str, str]:
    """Readiness: can I serve traffic? Fails when the database is unreachable."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "not_ready"}
    return {"status": "ready"}
