from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "graphql-gateway"
    sentry_dsn: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]

    # Resolver-level aggregation calls each service's own REST API — the
    # gateway never touches another service's database directly (see
    # docs/architecture.md). No resolver-level auth yet: that's wired in
    # Phase 6 alongside session/role auth in every other service.
    catalog_service_url: str = "http://localhost:5004"
    inventory_service_url: str = "http://localhost:5005"
    supplier_service_url: str = "http://localhost:5001"
    order_service_url: str = "http://localhost:5002"


settings = Settings()
