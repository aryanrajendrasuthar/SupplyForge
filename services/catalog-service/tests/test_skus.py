def _create_sku(client, **overrides):
    payload = {
        "sku": "WIDGET-1",
        "name": "Widget",
        "description": "A basic widget",
        "category": "widgets",
        "compliance_certs": ["RoHS"],
        "pricing_tiers": [{"min_quantity": 1, "unit_price": "9.99"}],
    }
    payload.update(overrides)
    return client.post("/skus", json=payload)


def test_create_sku_returns_201_with_body(client):
    response = _create_sku(client)
    assert response.status_code == 201
    body = response.get_json()
    assert body["sku"] == "WIDGET-1"
    assert body["pricing_tiers"] == [{"min_quantity": 1, "unit_price": "9.99"}]


def test_create_sku_rejects_duplicate(client):
    _create_sku(client)
    response = _create_sku(client)
    assert response.status_code == 409


def test_create_sku_rejects_invalid_payload(client):
    response = client.post("/skus", json={"sku": "", "name": "", "category": ""})
    assert response.status_code == 400


def test_get_sku_returns_created_sku(client):
    _create_sku(client)
    response = client.get("/skus/WIDGET-1")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Widget"


def test_get_sku_404_when_missing(client):
    response = client.get("/skus/NOPE")
    assert response.status_code == 404


def test_list_skus_filters_by_category(client):
    _create_sku(client, sku="WIDGET-1", category="widgets")
    _create_sku(client, sku="GADGET-1", category="gadgets")

    response = client.get("/skus?category=gadgets")
    body = response.get_json()
    assert [item["sku"] for item in body["items"]] == ["GADGET-1"]


def test_update_sku_changes_fields(client):
    _create_sku(client)
    response = client.patch("/skus/WIDGET-1", json={"name": "Deluxe Widget"})
    assert response.status_code == 200
    assert response.get_json()["name"] == "Deluxe Widget"


def test_update_sku_pricing_publishes_pricing_updated_event(client, event_publisher):
    _create_sku(client)
    response = client.patch(
        "/skus/WIDGET-1", json={"pricing_tiers": [{"min_quantity": 1, "unit_price": "12.50"}]}
    )
    assert response.status_code == 200
    assert len(event_publisher.events) == 1
    event_type, payload, _correlation_id = event_publisher.events[0]
    assert event_type == "pricing.updated"
    assert payload == {"sku": "WIDGET-1"}


def test_update_sku_without_pricing_change_does_not_publish_event(client, event_publisher):
    _create_sku(client)
    client.patch("/skus/WIDGET-1", json={"name": "Renamed"})
    assert event_publisher.events == []


def test_deactivate_sku_soft_deletes(client):
    _create_sku(client)
    response = client.delete("/skus/WIDGET-1")
    assert response.status_code == 204

    listed = client.get("/skus").get_json()
    assert listed["items"] == []

    # still directly retrievable, just excluded from active listings
    assert client.get("/skus/WIDGET-1").status_code == 200


def test_correlation_id_is_echoed_back(client):
    response = client.get("/skus", headers={"X-Correlation-ID": "test-corr-id"})
    assert response.headers["X-Correlation-ID"] == "test-corr-id"


def test_correlation_id_is_generated_when_absent(client):
    response = client.get("/skus")
    assert response.headers["X-Correlation-ID"]
