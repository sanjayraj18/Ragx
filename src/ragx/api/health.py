"""Liveness and readiness probes — different questions, different endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/healthz")
async def healthz() -> dict[str,str]:
    """Liveness: is the process running? Restart me if this fails."""
    return {"status" : "ok"}

@router.get("/readyz")
async def readyz() -> dict[str,str]:
    """Readiness: can I serve traffic? (Task 5 adds the real DB check.)"""
    return {"status": "ready"}