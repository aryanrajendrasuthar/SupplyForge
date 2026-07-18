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


def _register(client, **overrides):
    payload = {"legal_name": "Acme Supplies", "contact_email": "acme@example.com"}
    payload.update(overrides)
    return client.post("/suppliers", json=payload)


@pytest.fixture
def supplier_id(client):
    return _register(client).get_json()["id"]
