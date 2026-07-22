import fakeredis
import pytest
from supplyforge_auth.cookies import SESSION_COOKIE_NAME

from app import create_app
from app.config import settings


class FakeEventPublisher:
    def __init__(self):
        self.events: list[tuple[str, dict, str]] = []

    def publish(self, event_type: str, payload: dict, correlation_id: str) -> None:
        self.events.append((event_type, payload, correlation_id))


class FakeNotifier:
    def __init__(self):
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))


@pytest.fixture
def event_publisher():
    return FakeEventPublisher()


@pytest.fixture
def notifier():
    return FakeNotifier()


@pytest.fixture
def app(tmp_path, event_publisher, notifier):
    # SQLite (file-backed, not :memory:, so every connection in the pool sees
    # the same data) stands in for SQL Server in tests — no live DB needed in CI.
    settings.database_url = f"sqlite:///{tmp_path / 'test.db'}"
    # flask-limiter's in-memory backend — no live Redis needed in CI.
    settings.redis_url = "memory://"
    flask_app = create_app(redis_client=fakeredis.FakeRedis())
    flask_app.event_publisher = event_publisher
    flask_app.notifier = notifier
    flask_app.config.update(TESTING=True)
    yield flask_app
    flask_app.session_factory.remove()


@pytest.fixture
def anon_client(app):
    """An unauthenticated client — use this to test the 401 path itself."""
    return app.test_client()


@pytest.fixture
def client(app):
    """Pre-authenticated: order creation only requires *some* logged-in
    user, not a specific role, so every existing test gets a valid session
    without needing to log in explicitly (sessions are normally created by
    supplier-service's /auth/login; this injects one directly)."""
    test_client = app.test_client()
    token = app.session_store.create({"user_id": "test-user", "email": "test@example.com", "role": "analyst"})
    test_client.set_cookie(SESSION_COOKIE_NAME, token)
    return test_client
