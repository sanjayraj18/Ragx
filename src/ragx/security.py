"""Password hashing — the only module that knows the algorithm.

Passwords are never stored or recoverable: only an argon2 fingerprint is
kept. Hashing is deliberately slow and memory-hard so a stolen database
resists offline guessing at GPU scale."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from ragx.errors import UnauthorizedError

_hasher = PasswordHasher()
_ALGORITHM = "HS256"
_API_KEY_PREFIX = "ragx_"


def hashPassword(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashedPassword: str) -> bool:
    try:
        return _hasher.verify(hashedPassword, password)
    except VerifyMismatchError:
        return False


def create_access_token(
    *, user_id: uuid.UUID, tenant_id: uuid.UUID, secret_key: str, expires_minutes: int
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }

    return jwt.encode(payload, secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str, *, secret_key: str) -> dict[str, str]:
    try:
        return jwt.decode(token, secret_key, algorithms=[_ALGORITHM])
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("invalid or expired token") from exc


def generate_api_key() -> tuple[str, str]:
    """Return (plaintext, hash). The plaintext is shown once and never stored."""
    plain_text = _API_KEY_PREFIX + secrets.token_urlsafe(32)
    return plain_text, hash_api_key(plain_text)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
