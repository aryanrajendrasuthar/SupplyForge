import json

from app.validator import GroqValidator


class FakeResponse:
    def __init__(self, content: dict):
        self._content = content

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return {"choices": [{"message": {"content": json.dumps(self._content)}}]}


def test_validator_parses_groq_response_into_verdict(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return FakeResponse({"is_anomalous": True, "reason": "negative quantity"})

    monkeypatch.setattr("requests.post", fake_post)

    validator = GroqValidator(api_key="test-key", base_url="https://api.groq.com/openai/v1", model="test-model")
    verdict = validator.validate({"sku": "WIDGET-1", "quantity": -5})

    assert verdict == {"is_anomalous": True, "reason": "negative quantity"}
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["json"]["model"] == "test-model"


def test_validator_defaults_missing_fields(monkeypatch):
    monkeypatch.setattr("requests.post", lambda url, headers, json, timeout: FakeResponse({}))

    validator = GroqValidator(api_key="k", base_url="https://api.groq.com/openai/v1", model="m")
    verdict = validator.validate({"sku": "WIDGET-1"})

    assert verdict == {"is_anomalous": False, "reason": None}
