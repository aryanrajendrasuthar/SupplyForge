import requests

from app import clients
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


def test_fetch_skus_hits_catalog_service_and_unwraps_items(monkeypatch):
    captured = {}

    def fake_get(url, params, timeout):
        captured["url"] = url
        captured["params"] = params
        return FakeResponse({"items": [{"sku": "WIDGET-1"}], "page": 1, "page_size": 25})

    monkeypatch.setattr(requests, "get", fake_get)

    result = clients.fetch_skus(category="widgets")

    assert captured["url"] == f"{settings.catalog_service_url}/skus"
    assert captured["params"] == {"category": "widgets"}
    assert result == [{"sku": "WIDGET-1"}]


def test_fetch_sku_returns_none_on_404(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse({"error": "not found"}, status_code=404)

    monkeypatch.setattr(requests, "get", fake_get)

    assert clients.fetch_sku("NOPE") is None


def test_fetch_sku_reraises_non_404_errors(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse({"error": "boom"}, status_code=500)

    monkeypatch.setattr(requests, "get", fake_get)

    try:
        clients.fetch_sku("WIDGET-1")
        raised = False
    except requests.HTTPError:
        raised = True

    assert raised


def test_create_order_posts_payload(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return FakeResponse({"id": 1, **json, "status": "pending"})

    monkeypatch.setattr(requests, "post", fake_post)

    payload = {"customer_email": "c@example.com", "line_items": []}
    result = clients.create_order(payload)

    assert captured["url"] == f"{settings.order_service_url}/orders"
    assert result["status"] == "pending"
