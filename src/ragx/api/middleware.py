"""Request context middleware: every request gets an id, and that id is
  bound to the logging context so every log line the request causes carries it."""

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
          request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())

          structlog.contextvars.clear_contextvars()
          structlog.contextvars.bind_contextvars(request_id=request_id)
          
          response = await call_next(request)
          response.headers[REQUEST_ID_HEADER] = request_id
          return response