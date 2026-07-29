"""Password hashing — the only module that knows the algorithm.

  Passwords are never stored or recoverable: only an argon2 fingerprint is
  kept. Hashing is deliberately slow and memory-hard so a stolen database
  resists offline guessing at GPU scale."""


from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()

def hashPassword(password : str) -> str:
    return _hasher.hash(password)

def verify_password(password : str, hashedPassword : str) -> bool:
    try:
        return _hasher.verify(hashedPassword, password)
    except VerifyMismatchError:
          return False

