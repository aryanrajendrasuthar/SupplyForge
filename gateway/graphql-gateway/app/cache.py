import json

_KEY_PREFIX = "cache:sku:"
_DEFAULT_TTL_SECONDS = 300  # 5 minutes — a backstop against a missed/delayed
# invalidation message, not the primary way this is meant to expire.


class SkuCache:
    """Caches individual SKU lookups, invalidated by app/consumer.py the
    moment catalog-service publishes pricing.updated — event-driven, not
    TTL-only (see docs/architecture.md)."""

    def __init__(self, redis_client, ttl_seconds: int = _DEFAULT_TTL_SECONDS):
        self._redis = redis_client
        self._ttl = ttl_seconds

    def get(self, sku: str) -> dict | None:
        raw = self._redis.get(_KEY_PREFIX + sku)
        return json.loads(raw) if raw is not None else None

    def set(self, sku: str, value: dict) -> None:
        self._redis.set(_KEY_PREFIX + sku, json.dumps(value), ex=self._ttl)

    def invalidate(self, sku: str) -> None:
        self._redis.delete(_KEY_PREFIX + sku)
