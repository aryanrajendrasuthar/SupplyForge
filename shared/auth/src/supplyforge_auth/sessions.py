import secrets
from datetime import timedelta

from redis import Redis

_KEY_PREFIX = "session:"


class SessionStore:
    """Redis-backed session tokens: 256-bit random values, server-side revocation."""

    def __init__(self, redis_client: Redis, ttl: timedelta = timedelta(hours=12)):
        self._redis = redis_client
        self._ttl = ttl

    def create(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)  # 256 bits of entropy
        self._redis.set(_KEY_PREFIX + token, user_id, ex=self._ttl)
        return token

    def resolve(self, token: str) -> str | None:
        user_id = self._redis.get(_KEY_PREFIX + token)
        return user_id.decode() if user_id is not None else None

    def revoke(self, token: str) -> None:
        self._redis.delete(_KEY_PREFIX + token)

    def revoke_all_for_user(self, user_id: str) -> None:
        """Scans and revokes every session belonging to a user (e.g. on password change)."""
        for key in self._redis.scan_iter(match=_KEY_PREFIX + "*"):
            if self._redis.get(key) == user_id.encode():
                self._redis.delete(key)
