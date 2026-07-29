"""Password hashing — the only module that knows the algorithm.

  Passwords are never stored or recoverable: only an argon2 fingerprint is
  kept. Hashing is deliberately slow and memory-hard so a stolen database
  resists offline guessing at GPU scale."""


import datetime
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt

from ragx.errors import UnauthorizedError

_hasher = PasswordHasher()
_ALGORITHM = "HS256"

def hashPassword(password : str) -> str:
    return _hasher.hash(password)

def verify_password(password : str, hashedPassword : str) -> bool:
    try:
        return _hasher.verify(hashedPassword, password)
    except VerifyMismatchError:
          return False

def create_access_token(*, user_id:uuid.UUID, tenant_id:uuid.UUID,secret_key: str, expires_minutes : int) -> str:
     now = datetime.now(datetime.UTC)
     payload = {
          "sub" : str(user_id),
          "tid" : str(tenant_id),
          "iat" : now,
          "exp" : now + datetime.timedelta(minutes=expires_minutes),
     }

     return jwt.encode(payload,secret_key, algorithm=_ALGORITHM);

def decode_access_token(token : str, secret_key : str) -> dict[str,str]:
    try:
        return jwt.verify(token, secret_key,algorithm=_ALGORITHM)
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("invalid or expired token") from exc
