from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "supplier-service"
    sentry_dsn: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]

    # SQL Server in dev/prod; tests override this to a file-backed SQLite DB
    # (see tests/conftest.py) so CI doesn't need a live database.
    database_url: str = "mssql+pymssql://sa:ChangeMe_Dev123!@localhost:1433/supplier_service"

    # Sessions + rate-limit counters. docker-compose supplies the real
    # authenticated URL via env var; this default assumes a no-auth local
    # Redis. Tests inject a fakeredis client directly (see tests/conftest.py)
    # rather than using this setting at all.
    redis_url: str = "redis://localhost:6380/0"
    rate_limit_default: str = "200 per hour"
    rate_limit_auth: str = "10 per 15 minutes"


settings = Settings()
