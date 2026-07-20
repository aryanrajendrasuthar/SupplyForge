import mongomock
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
def app(event_publisher):
    # mongomock stands in for a real MongoDB connection in tests — no live
    # database needed in CI, consistent with the SQLite-for-SQL approach
    # used in the SQL-Server-backed services.
    collection = mongomock.MongoClient().db.records
    # flask-limiter's in-memory backend — no live Redis needed in CI.
    settings.redis_url = "memory://"
    flask_app = create_app(records_collection=collection)
    flask_app.event_publisher = event_publisher
    flask_app.config.update(TESTING=True)
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()
