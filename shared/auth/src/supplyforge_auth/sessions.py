import json
import secrets
from datetime import timedelta

from redis import Redis

_KEY_PREFIX = "session:"


class SessionStore:
    """Redis-backed session tokens: 256-bit random values, server-side revocation.

    Session data is an arbitrary JSON-serializable dict (must include
    "user_id") rather than a bare user ID, so any service holding the same
    Redis connection can resolve a session and read the caller's role
    without needing its own copy of the user/account table.
    """

    def __init__(self, redis_client: Redis, ttl: timedelta = timedelta(hours=12)):
        self._redis = redis_client
        self._ttl = ttl

    def create(self, session_data: dict) -> str:
        token = secrets.token_urlsafe(32)  # 256 bits of entropy
        self._redis.set(_KEY_PREFIX + token, json.dumps(session_data), ex=self._ttl)
        return token

    def resolve(self, token: str) -> dict | None:
        raw = self._redis.get(_KEY_PREFIX + token)
        return json.loads(raw) if raw is not None else None

    def revoke(self, token: str) -> None:
        self._redis.delete(_KEY_PREFIX + token)

    def revoke_all_for_user(self, user_id: str) -> None:
        """Scans and revokes every session belonging to a user (e.g. on password change)."""
        for key in self._redis.scan_iter(match=_KEY_PREFIX + "*"):
            raw = self._redis.get(key)
            if raw is not None and json.loads(raw).get("user_id") == user_id:
                self._redis.delete(key)
