from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "order-service"
    sentry_dsn: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]

    # SQL Server in dev/prod; tests override this to a file-backed SQLite DB
    # (see tests/conftest.py) so CI doesn't need a live database.
    database_url: str = "mssql+pymssql://sa:ChangeMe_Dev123!@localhost:1433/order_service"

    # ElasticMQ locally (SQS-API-compatible); swap to real AWS SQS in prod by
    # changing the endpoint only.
    sqs_endpoint_url: str = "http://localhost:9324"
    reservation_queue_url: str = "http://localhost:9324/000000000000/inventory-reservation-queue"
    order_status_queue_url: str = "http://localhost:9324/000000000000/order-status-queue"

    # Session validation (sessions are created by supplier-service's
    # /auth/login — every service resolves them off the same Redis, no
    # shared Users table) and rate-limit counters. docker-compose supplies
    # the real authenticated URL via env var; this default assumes a no-auth
    # local Redis. Tests inject a fakeredis client directly.
    redis_url: str = "redis://localhost:6380/0"
    rate_limit_default: str = "200 per hour"


settings = Settings()
