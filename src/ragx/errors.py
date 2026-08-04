"""Domain exception hierarchy.

Services raise these to say WHAT happened ("document not found"), never
how to respond over HTTP. The API boundary translates them to responses
in exactly one place. Expected failures only — bugs don't get classes.
"""


class RagxError(Exception):
    """Base class for all expected application errors."""

    code = "internal_error"
    status_code = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(RagxError):
    code = "not_found"
    status_code = 404


class ConflictError(RagxError):
    code = "conflict"
    status_code = 409


class UnauthorizedError(RagxError):
    code = "unauthorized"
    status_code = 401


class PayloadTooLargeError(RagxError):
    code = "payload_too_large"
    status_code = 413


class UnsupportedMediaTypeError(RagxError):
    code = "unsupported_media_type"
    status_code = 415


class EmbeddingError(RagxError):
    code = "embedding_failed"
    status_code = 502
