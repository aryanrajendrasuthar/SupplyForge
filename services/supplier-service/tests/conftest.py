import fakeredis
import pytest

from app import create_app
from app.config import settings


@pytest.fixture
def app(tmp_path):
    # SQLite (file-backed, not :memory:, so every connection in the pool sees
    # the same data) stands in for SQL Server in tests — no live DB needed in CI.
    settings.database_url = f"sqlite:///{tmp_path / 'test.db'}"
    # flask-limiter's in-memory backend — no live Redis needed in CI. Session
    # storage is separately injected below via fakeredis.
    settings.redis_url = "memory://"
    flask_app = create_app(redis_client=fakeredis.FakeRedis())
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


def _login_as(client, email: str, role: str) -> None:
    """Registers and logs in a user, leaving the session cookie set on `client`."""
    password = "correct horse battery staple"
    client.post("/auth/register", json={"email": email, "password": password, "role": role})
    client.post("/auth/login", json={"email": email, "password": password})


@pytest.fixture
def approver_client(client):
    _login_as(client, "approver@example.com", "approver")
    return client


@pytest.fixture
def admin_client(client):
    _login_as(client, "admin@example.com", "admin")
    return client
