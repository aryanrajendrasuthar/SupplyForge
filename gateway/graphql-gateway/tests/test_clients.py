import fakeredis
import pytest
import requests

from app import clients, create_app
from app.config import settings


class FakeResponse:
    def __init__(self, json_body, status_code=200):
        self._json_body = json_body
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(response=self)
            raise error

    def json(self):
        return self._json_body


@pytest.fixture
def request_context():
    # flask-limiter's in-memory backend — no live Redis needed in CI. The
    # SKU cache gets a fakeredis client directly since settings.redis_url
    # can't double as a redis.Redis.from_url() target once it's "memory://".
    settings.redis_url = "memory://"
    # clients.py reads request.cookies to forward the caller's session to
    # the backend service — needs an active Flask request context, unlike a
    # bare function call.
    app = create_app(redis_client=fakeredis.FakeRedis())
    with app.test_request_context(headers={"Cookie": "sf_session=test-token"}):
        yield


def test_fetch_skus_hits_catalog_service_and_unwraps_items(monkeypatch, request_context):
    captured = {}

    def fake_get(url, params, cookies, timeout):
        captured["url"] = url
        captured["params"] = params
        captured["cookies"] = cookies
        return FakeResponse({"items": [{"sku": "WIDGET-1"}], "page": 1, "page_size": 25})

    monkeypatch.setattr(requests, "get", fake_get)

    result = clients.fetch_skus(category="widgets")

    assert captured["url"] == f"{settings.catalog_service_url}/skus"
    assert captured["params"] == {"category": "widgets"}
    assert captured["cookies"] == {"sf_session": "test-token"}
    assert result == [{"sku": "WIDGET-1"}]


def test_fetch_sku_returns_none_on_404(monkeypatch, request_context):
    def fake_get(url, params, cookies, timeout):
        return FakeResponse({"error": "not found"}, status_code=404)

    monkeypatch.setattr(requests, "get", fake_get)

    assert clients.fetch_sku("NOPE") is None


def test_fetch_sku_is_cached_after_first_lookup(monkeypatch, request_context):
    call_count = 0

    def fake_get(url, params, cookies, timeout):
        nonlocal call_count
        call_count += 1
        return FakeResponse({"sku": "WIDGET-1"})

    monkeypatch.setattr(requests, "get", fake_get)

    assert clients.fetch_sku("WIDGET-1") == {"sku": "WIDGET-1"}
    assert clients.fetch_sku("WIDGET-1") == {"sku": "WIDGET-1"}
    assert call_count == 1  # second lookup served from cache, no second REST call


def test_fetch_sku_reraises_non_404_errors(monkeypatch, request_context):
    def fake_get(url, params, cookies, timeout):
        return FakeResponse({"error": "boom"}, status_code=500)

    monkeypatch.setattr(requests, "get", fake_get)

    try:
        clients.fetch_sku("WIDGET-1")
        raised = False
    except requests.HTTPError:
        raised = True

    assert raised


def test_create_order_posts_payload_and_forwards_session_cookie(monkeypatch, request_context):
    captured = {}

    def fake_post(url, json, cookies, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["cookies"] = cookies
        return FakeResponse({"id": 1, **json, "status": "pending"})

    monkeypatch.setattr(requests, "post", fake_post)

    payload = {"customer_email": "c@example.com", "line_items": []}
    result = clients.create_order(payload)

    assert captured["url"] == f"{settings.order_service_url}/orders"
    assert captured["cookies"] == {"sf_session": "test-token"}
    assert result["status"] == "pending"
