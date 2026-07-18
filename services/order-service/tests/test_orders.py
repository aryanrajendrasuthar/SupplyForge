def _create_order(client, **overrides):
    payload = {
        "customer_email": "customer@example.com",
        "line_items": [{"sku": "WIDGET-1", "warehouse_code": "WH1", "quantity": 2}],
    }
    payload.update(overrides)
    return client.post("/orders", json=payload)


def test_create_order_returns_201_pending(client):
    response = _create_order(client)
    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "pending"
    assert body["line_items"] == [{"sku": "WIDGET-1", "warehouse_code": "WH1", "quantity": 2}]


def test_create_order_publishes_order_created_event(client, event_publisher):
    response = _create_order(client)
    order_id = response.get_json()["id"]

    assert len(event_publisher.events) == 1
    event_type, payload, _correlation_id = event_publisher.events[0]
    assert event_type == "order.created"
    assert payload["order_id"] == order_id
    assert payload["line_items"] == [{"sku": "WIDGET-1", "warehouse_code": "WH1", "quantity": 2}]


def test_create_order_rejects_empty_line_items(client):
    response = client.post("/orders", json={"customer_email": "c@example.com", "line_items": []})
    assert response.status_code == 400


def test_create_order_rejects_invalid_email(client):
    response = client.post(
        "/orders",
        json={"customer_email": "nope", "line_items": [{"sku": "A", "warehouse_code": "WH1", "quantity": 1}]},
    )
    assert response.status_code == 400


def test_get_order_404_when_missing(client):
    assert client.get("/orders/9999").status_code == 404


def test_list_orders_filters_by_status(client):
    _create_order(client)
    response = client.get("/orders?status=pending")
    assert len(response.get_json()) == 1

    response = client.get("/orders?status=confirmed")
    assert response.get_json() == []
