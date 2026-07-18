import pytest

from app import create_app
from app.config import settings


@pytest.fixture
def app(tmp_path):
    # SQLite (file-backed, not :memory:, so every connection in the pool sees
    # the same data) stands in for SQL Server in tests — no live DB needed in CI.
    settings.database_url = f"sqlite:///{tmp_path / 'test.db'}"
    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    yield flask_app
    flask_app.session_factory.remove()


@pytest.fixture
def client(app):
    return app.test_client()


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
