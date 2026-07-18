from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ai-validation-worker"

    # ElasticMQ locally (SQS-API-compatible); swap to real AWS SQS in prod by
    # changing the endpoint only.
    sqs_endpoint_url: str = "http://localhost:9324"
    ai_validation_queue_url: str = "http://localhost:9324/000000000000/ai-validation-queue"
    validation_result_queue_url: str = "http://localhost:9324/000000000000/validation-result-queue"

    # Groq is the AI-assisted validation provider (see docs/project-plan.md
    # §1). No key is required to run the test suite — tests inject a fake
    # Validator instead of calling Groq (see tests/test_handler.py).
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.1-8b-instant"


settings = Settings()
