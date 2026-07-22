from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "graphql-gateway"
    sentry_dsn: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]

    # Resolver-level aggregation calls each service's own REST API — the
    # gateway never touches another service's database directly (see
    # docs/architecture.md). Auth is enforced at each backend service (see
    # require_session() there); the gateway's job is just to forward the
    # caller's session cookie along (see app/clients.py), not re-check it.
    catalog_service_url: str = "http://localhost:5004"
    inventory_service_url: str = "http://localhost:5005"
    supplier_service_url: str = "http://localhost:5001"
    order_service_url: str = "http://localhost:5002"

    # Rate-limit counters and the SKU pricing cache. docker-compose supplies
    # the real authenticated Redis URL via env var; this default assumes a
    # no-auth local Redis.
    redis_url: str = "redis://localhost:6380/0"
    rate_limit_default: str = "200 per hour"

    # ElasticMQ locally (SQS-API-compatible); swap to real AWS SQS in prod by
    # changing the endpoint only. Only app/consumer.py uses these — it
    # invalidates the SKU cache when catalog-service publishes
    # pricing.updated, rather than leaving stale prices to expire off a bare
    # TTL (see docs/architecture.md).
    sqs_endpoint_url: str = "http://localhost:9324"
    pricing_queue_url: str = "http://localhost:9324/000000000000/pricing-invalidation-queue"


settings = Settings()
