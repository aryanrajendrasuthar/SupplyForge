from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher(type=Type.ID)


def hash_password(plaintext: str) -> str:
    return _hasher.hash(plaintext)


def verify_password(plaintext: str, stored_hash: str) -> bool:
    try:
        return _hasher.verify(stored_hash, plaintext)
    except VerifyMismatchError:
        return False


def needs_rehash(stored_hash: str) -> bool:
    """True if the hash was created with weaker params than current defaults."""
    return _hasher.check_needs_rehash(stored_hash)
