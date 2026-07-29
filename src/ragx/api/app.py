"""Application factory.

The app is built by calling create_app(), never at import time: importing
this module has zero consequences. Each call returns a fresh, private app
configured by the Settings it was given (or the environment's, if none).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ragx.api.auth import router as auth_router
from ragx.api.health import router as health_router
from ragx.api.middleware import RequestContextMiddleware
from ragx.config import Settings, get_settings
from ragx.db.session import create_engine, create_session_factory
from ragx.errors import RagxError
from ragx.logging import configure_logging, get_logger

log = get_logger(__name__)

def _error_response(status_code : int, code : str, message : str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def create_app(settings : Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    @asynccontextmanager
    async def lifespan(app : FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings)
        app.state.session_factory = create_session_factory(engine)
        app.state.settings = settings
        log.info("app_started", environment=settings.environment)
        yield
        await engine.dispose()
        log.info("app_stopped")

    app = FastAPI(
          title=settings.app_name,
          debug=settings.debug,
          lifespan=lifespan,
      )

    app.add_middleware(RequestContextMiddleware)
    app.include_router(health_router)
    app.include_router(auth_router)

    @app.exception_handler(RagxError)
    async def handle_domain_error(request: Request, exc: RagxError) ->JSONResponse:
        log.warning("request_failed", code=exc.code, error=exc.message)
        return _error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled_exception", exc_info=exc)
        return _error_response(500, "internal_error", "An internal error occurred.")

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error_response(exc.status_code, "http_error", str(exc.detail))


    return app
