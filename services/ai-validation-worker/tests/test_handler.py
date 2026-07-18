import pytest

from app.handler import process_message


class FakeValidator:
    def __init__(self, verdict):
        self._verdict = verdict

    def validate(self, payload: dict) -> dict:
        return self._verdict


def test_process_message_returns_clean_verdict():
    event = {"record_id": "rec-1", "payload": {"sku": "WIDGET-1", "quantity": 10}}
    validator = FakeValidator({"is_anomalous": False, "reason": None})

    result = process_message(event, validator)

    assert result == {"record_id": "rec-1", "is_anomalous": False, "reason": None}


def test_process_message_returns_anomalous_verdict_with_reason():
    event = {"record_id": "rec-2", "payload": {"sku": "WIDGET-1", "quantity": -5}}
    validator = FakeValidator({"is_anomalous": True, "reason": "negative quantity"})

    result = process_message(event, validator)

    assert result == {"record_id": "rec-2", "is_anomalous": True, "reason": "negative quantity"}


def test_process_message_propagates_validator_errors():
    class FailingValidator:
        def validate(self, payload: dict) -> dict:
            raise RuntimeError("Groq request failed")

    with pytest.raises(RuntimeError):
        process_message({"record_id": "rec-3", "payload": {}}, FailingValidator())
