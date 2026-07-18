import json

from flask import Blueprint, current_app, g, jsonify, request
from pydantic import ValidationError

from app.bulk_ingest import parse_bulk_ingest
from app.repository import get_record, insert_record, list_records
from app.schemas import IngestRecord

bp = Blueprint("ingestion", __name__)


def _record_out(document: dict) -> dict:
    return {
        "id": str(document["_id"]),
        "source": document["source"],
        "payload": document["payload"],
        "status": document["status"],
        "verdict": document.get("verdict"),
    }


def _publish_for_validation(record_id: str, source: str, payload: dict, correlation_id: str) -> None:
    current_app.event_publisher.publish(
        "ingestion.record_received",
        {"record_id": record_id, "source": source, "payload": payload},
        correlation_id,
    )


@bp.post("/ingest")
def ingest():
    try:
        payload = IngestRecord.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400

    document = insert_record(g.records, payload.source, payload.payload)
    _publish_for_validation(str(document["_id"]), payload.source, payload.payload, g.get("correlation_id", ""))
    return jsonify(_record_out(document)), 202


@bp.post("/ingest/bulk")
def ingest_bulk():
    file = request.files.get("file")
    source = request.form.get("source")
    if file is None or not source:
        return jsonify({"error": "file and source are required"}), 400

    try:
        rows = parse_bulk_ingest(file.filename or "", file.read())
    except (ValueError, json.JSONDecodeError) as exc:
        return jsonify({"error": str(exc)}), 400

    record_ids = []
    for row in rows:
        document = insert_record(g.records, source, row)
        _publish_for_validation(str(document["_id"]), source, row, g.get("correlation_id", ""))
        record_ids.append(str(document["_id"]))

    return jsonify({"accepted": len(record_ids), "record_ids": record_ids}), 200


@bp.get("/records/<record_id>")
def get_record_route(record_id: str):
    document = get_record(g.records, record_id)
    if document is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(_record_out(document))


@bp.get("/records")
def list_records_route():
    status = request.args.get("status")
    documents = list_records(g.records, status)
    return jsonify([_record_out(d) for d in documents])
