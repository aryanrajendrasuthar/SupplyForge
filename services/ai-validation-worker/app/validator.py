import json
from typing import Protocol, TypedDict


class ValidationVerdict(TypedDict):
    is_anomalous: bool
    reason: str | None


class Validator(Protocol):
    def validate(self, payload: dict) -> ValidationVerdict: ...


_SYSTEM_PROMPT = (
    "You are a data-quality checker for supply-chain records (inventory, orders, "
    "catalog entries). Given a JSON record, decide if it looks anomalous: "
    "negative or zero quantities/prices, missing required identifiers, or values "
    "wildly outside a plausible range. Respond with ONLY a JSON object: "
    '{"is_anomalous": true|false, "reason": "<short reason or null>"}.'
)


class GroqValidator:
    """Calls Groq's OpenAI-compatible chat completions endpoint."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self._api_key = api_key
        self._base_url = base_url
        self._model = model

    def validate(self, payload: dict) -> ValidationVerdict:
        import requests

        response = requests.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload)},
                ],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
            timeout=15,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        verdict = json.loads(content)
        return {"is_anomalous": bool(verdict.get("is_anomalous", False)), "reason": verdict.get("reason")}
