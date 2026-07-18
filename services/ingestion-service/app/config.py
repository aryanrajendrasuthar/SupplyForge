from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ingestion-service"
    sentry_dsn: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]

    # MongoDB locally and in prod (Atlas free tier) — see docs/project-plan.md §1.
    # No credentials embedded here: set MONGO_URL in .env if your local Mongo
    # requires auth (infra/docker-compose.yml passes it via env, not this default).
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db_name: str = "ingestion_service"

    # ElasticMQ locally (SQS-API-compatible); swap to real AWS SQS in prod by
    # changing the endpoint only.
    sqs_endpoint_url: str = "http://localhost:9324"
    ai_validation_queue_url: str = "http://localhost:9324/000000000000/ai-validation-queue"
    validation_result_queue_url: str = "http://localhost:9324/000000000000/validation-result-queue"


settings = Settings()
