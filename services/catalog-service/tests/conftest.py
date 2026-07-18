import pytest

from app import create_app
from app.config import settings


class FakeEventPublisher:
    def __init__(self):
        self.events: list[tuple[str, dict, str]] = []

    def publish(self, event_type: str, payload: dict, correlation_id: str) -> None:
        self.events.append((event_type, payload, correlation_id))


@pytest.fixture
def event_publisher():
    return FakeEventPublisher()


@pytest.fixture
def app(tmp_path, event_publisher):
    # SQLite (file-backed, not :memory:, so every connection in the pool sees
    # the same data) stands in for SQL Server in tests — no live DB needed in CI.
    settings.database_url = f"sqlite:///{tmp_path / 'test.db'}"
    flask_app = create_app()
    flask_app.event_publisher = event_publisher
    flask_app.config.update(TESTING=True)
    yield flask_app
    flask_app.session_factory.remove()


@pytest.fixture
def client(app):
    return app.test_client()
