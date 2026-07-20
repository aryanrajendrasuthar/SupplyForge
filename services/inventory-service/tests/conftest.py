import fakeredis
import pytest
from supplyforge_auth.cookies import SESSION_COOKIE_NAME

from app import create_app
from app.config import settings


@pytest.fixture
def app(tmp_path):
    # SQLite (file-backed, not :memory:, so every connection in the pool sees
    # the same data) stands in for SQL Server in tests — no live DB needed in CI.
    settings.database_url = f"sqlite:///{tmp_path / 'test.db'}"
    # flask-limiter's in-memory backend — no live Redis needed in CI.
    settings.redis_url = "memory://"
    flask_app = create_app(redis_client=fakeredis.FakeRedis())
    flask_app.config.update(TESTING=True)
    yield flask_app
    flask_app.session_factory.remove()


@pytest.fixture
def anon_client(app):
    """An unauthenticated client — use this to test the 401 path itself."""
    return app.test_client()


@pytest.fixture
def client(app):
    """Pre-authenticated: warehouse/stock setup only requires *some*
    logged-in user, not a specific role, so every existing test gets a
    valid session without needing to log in explicitly (sessions are
    normally created by supplier-service's /auth/login; this injects one
    directly)."""
    test_client = app.test_client()
    token = app.session_store.create({"user_id": "test-user", "email": "test@example.com", "role": "analyst"})
    test_client.set_cookie(SESSION_COOKIE_NAME, token)
    return test_client


@pytest.fixture
def warehouse(client):
    client.post("/warehouses", json={"code": "WH1", "name": "Main Warehouse"})
    return "WH1"


@pytest.fixture
def stock_item(client, warehouse):
    client.post(
        "/stock",
        json={"warehouse_code": warehouse, "sku": "WIDGET-1", "quantity_on_hand": 10, "reorder_threshold": 2},
    )
    return warehouse, "WIDGET-1"
