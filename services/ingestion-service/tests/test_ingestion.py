import io
import json


def test_ingest_single_record_returns_202_pending(client):
    response = client.post(
        "/ingest", json={"source": "supplier-portal", "payload": {"sku": "WIDGET-1", "quantity": 10}}
    )
    assert response.status_code == 202
    body = response.get_json()
    assert body["status"] == "pending_validation"
    assert body["verdict"] is None
    assert body["payload"] == {"sku": "WIDGET-1", "quantity": 10}


def test_ingest_publishes_event_without_waiting_on_validation(client, event_publisher):
    response = client.post("/ingest", json={"source": "supplier-portal", "payload": {"sku": "WIDGET-1"}})
    record_id = response.get_json()["id"]

    assert len(event_publisher.events) == 1
    event_type, payload, _correlation_id = event_publisher.events[0]
    assert event_type == "ingestion.record_received"
    assert payload["record_id"] == record_id


def test_ingest_rejects_missing_source(client):
    response = client.post("/ingest", json={"payload": {"a": 1}})
    assert response.status_code == 400


def test_get_record_returns_404_when_missing(client):
    assert client.get("/records/000000000000000000000000").status_code == 404


def test_get_record_returns_invalid_id_as_404(client):
    assert client.get("/records/not-a-valid-object-id").status_code == 404


def test_list_records_filters_by_status(client):
    client.post("/ingest", json={"source": "s1", "payload": {"a": 1}})
    response = client.get("/records?status=pending_validation")
    assert len(response.get_json()) == 1

    response = client.get("/records?status=validated")
    assert response.get_json() == []


def test_bulk_ingest_json_creates_one_record_per_item(client):
    payload = [{"sku": "A"}, {"sku": "B"}]
    data = {"file": (io.BytesIO(json.dumps(payload).encode()), "records.json"), "source": "bulk-upload"}
    response = client.post("/ingest/bulk", data=data, content_type="multipart/form-data")

    assert response.status_code == 200
    body = response.get_json()
    assert body["accepted"] == 2
    assert len(body["record_ids"]) == 2


def test_bulk_ingest_csv_creates_one_record_per_row(client):
    csv_content = "sku,quantity\nWIDGET-1,5\nGADGET-1,3\n"
    data = {"file": (io.BytesIO(csv_content.encode()), "records.csv"), "source": "bulk-upload"}
    response = client.post("/ingest/bulk", data=data, content_type="multipart/form-data")

    assert response.status_code == 200
    body = response.get_json()
    assert body["accepted"] == 2

    record = client.get(f"/records/{body['record_ids'][0]}").get_json()
    assert record["payload"] == {"sku": "WIDGET-1", "quantity": "5"}


def test_bulk_ingest_requires_file_and_source(client):
    response = client.post("/ingest/bulk", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
