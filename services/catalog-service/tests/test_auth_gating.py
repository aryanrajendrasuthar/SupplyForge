import io


def test_create_sku_requires_authentication(anon_client):
    response = anon_client.post(
        "/skus", json={"sku": "WIDGET-1", "name": "Widget", "category": "widgets"}
    )
    assert response.status_code == 401


def test_list_skus_does_not_require_authentication(anon_client):
    # Reads stay open — only mutations are gated.
    assert anon_client.get("/skus").status_code == 200


def test_update_sku_requires_authentication(client, anon_client):
    client.post("/skus", json={"sku": "WIDGET-1", "name": "Widget", "category": "widgets"})
    response = anon_client.patch("/skus/WIDGET-1", json={"name": "Renamed"})
    assert response.status_code == 401


def test_deactivate_sku_requires_authentication(client, anon_client):
    client.post("/skus", json={"sku": "WIDGET-1", "name": "Widget", "category": "widgets"})
    response = anon_client.delete("/skus/WIDGET-1")
    assert response.status_code == 401


def test_bulk_import_requires_authentication(anon_client):
    data = {"file": (io.BytesIO(b"[]"), "skus.json")}
    response = anon_client.post("/skus/bulk-import", data=data, content_type="multipart/form-data")
    assert response.status_code == 401
