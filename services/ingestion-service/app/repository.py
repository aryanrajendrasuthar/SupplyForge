from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def insert_record(collection, source: str, payload: dict) -> dict:
    document = {
        "source": source,
        "payload": payload,
        "status": "pending_validation",
        "verdict": None,
        "received_at": _utcnow(),
    }
    result = collection.insert_one(document)
    document["_id"] = result.inserted_id
    return document


def get_record(collection, record_id: str) -> dict | None:
    try:
        object_id = ObjectId(record_id)
    except InvalidId:
        return None
    return collection.find_one({"_id": object_id})


def list_records(collection, status: str | None = None) -> list[dict]:
    query = {"status": status} if status else {}
    return list(collection.find(query).sort("received_at", 1))


def apply_validation_result(collection, record_id: str, is_anomalous: bool, reason: str | None) -> None:
    try:
        object_id = ObjectId(record_id)
    except InvalidId:
        return
    collection.update_one(
        {"_id": object_id},
        {"$set": {"status": "validated", "verdict": {"is_anomalous": is_anomalous, "reason": reason}}},
    )
