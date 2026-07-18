from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "inventory-service"
    sentry_dsn: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]

    # SQL Server in dev/prod; tests override this to an in-memory SQLite DB
    # (see tests/conftest.py) so CI doesn't need a live database.
    database_url: str = "mssql+pymssql://sa:ChangeMe_Dev123!@localhost:1433/inventory_service"

    # ElasticMQ locally (SQS-API-compatible); swap to real AWS SQS in prod by
    # changing the endpoint only.
    sqs_endpoint_url: str = "http://localhost:9324"
    reservation_queue_url: str = "http://localhost:9324/000000000000/inventory-reservation-queue"
    order_status_queue_url: str = "http://localhost:9324/000000000000/order-status-queue"


settings = Settings()
