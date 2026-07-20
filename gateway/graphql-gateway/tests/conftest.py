import pytest

from app import create_app
from app.config import settings


@pytest.fixture
def client():
    # flask-limiter's in-memory backend — no live Redis needed in CI.
    settings.redis_url = "memory://"
    return create_app().test_client()
