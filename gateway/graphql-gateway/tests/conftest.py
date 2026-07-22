import fakeredis
import pytest

from app import create_app
from app.config import settings


@pytest.fixture
def client():
    # flask-limiter's in-memory backend — no live Redis needed in CI. The
    # SKU cache gets a fakeredis client directly (see create_app's
    # redis_client override) since settings.redis_url can't double as a
    # redis.Redis.from_url() target once it's "memory://".
    settings.redis_url = "memory://"
    return create_app(redis_client=fakeredis.FakeRedis()).test_client()
