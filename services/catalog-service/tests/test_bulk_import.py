import io
import json


def test_bulk_import_json_creates_new_skus(client):
    payload = [
        {
            "sku": "BOLT-1",
            "name": "Bolt",
            "category": "hardware",
            "compliance_certs": [],
            "pricing_tiers": [{"min_quantity": 1, "unit_price": "0.50"}],
        },
        {
            "sku": "NUT-1",
            "name": "Nut",
            "category": "hardware",
            "compliance_certs": [],
            "pricing_tiers": [],
        },
    ]
    data = {"file": (io.BytesIO(json.dumps(payload).encode()), "skus.json")}
    response = client.post("/skus/bulk-import", data=data, content_type="multipart/form-data")

    assert response.status_code == 200
    body = response.get_json()
    assert body["created"] == 2
    assert body["updated"] == 0
    assert body["failed"] == 0

    assert client.get("/skus/BOLT-1").status_code == 200
    assert client.get("/skus/NUT-1").status_code == 200


def test_bulk_import_json_updates_existing_sku(client):
    create_payload = [{"sku": "BOLT-1", "name": "Bolt", "category": "hardware"}]
    client.post(
        "/skus/bulk-import",
        data={"file": (io.BytesIO(json.dumps(create_payload).encode()), "skus.json")},
        content_type="multipart/form-data",
    )

    update_payload = [{"sku": "BOLT-1", "name": "Renamed Bolt", "category": "hardware"}]
    response = client.post(
        "/skus/bulk-import",
        data={"file": (io.BytesIO(json.dumps(update_payload).encode()), "skus.json")},
        content_type="multipart/form-data",
    )

    body = response.get_json()
    assert body["updated"] == 1
    assert client.get("/skus/BOLT-1").get_json()["name"] == "Renamed Bolt"


def test_bulk_import_json_reports_row_level_failures(client):
    payload = [
        {"sku": "GOOD-1", "name": "Good", "category": "misc"},
        {"sku": "", "name": "", "category": ""},
    ]
    data = {"file": (io.BytesIO(json.dumps(payload).encode()), "skus.json")}
    response = client.post("/skus/bulk-import", data=data, content_type="multipart/form-data")

    body = response.get_json()
    assert body["created"] == 1
    assert body["failed"] == 1
    assert body["rows"][1]["status"] == "failed"
    assert body["rows"][1]["error"]


def test_bulk_import_csv_creates_skus_with_base_price(client):
    csv_content = (
        "sku,name,description,category,compliance_certs,unit_price\n"
        "SCREW-1,Screw,A screw,hardware,RoHS;CE,1.25\n"
    )
    data = {"file": (io.BytesIO(csv_content.encode()), "skus.csv")}
    response = client.post("/skus/bulk-import", data=data, content_type="multipart/form-data")

    assert response.status_code == 200
    body = response.get_json()
    assert body["created"] == 1

    sku = client.get("/skus/SCREW-1").get_json()
    assert sku["compliance_certs"] == ["RoHS", "CE"]
    assert sku["pricing_tiers"] == [{"min_quantity": 1, "unit_price": "1.25"}]


def test_bulk_import_requires_a_file(client):
    response = client.post("/skus/bulk-import", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
