def test_create_warehouse_returns_201(client):
    response = client.post("/warehouses", json={"code": "WH1", "name": "Main Warehouse"})
    assert response.status_code == 201
    assert response.get_json() == {"code": "WH1", "name": "Main Warehouse"}


def test_create_warehouse_rejects_duplicate_code(client, warehouse):
    response = client.post("/warehouses", json={"code": "WH1", "name": "Duplicate"})
    assert response.status_code == 409


def test_create_stock_item_requires_existing_warehouse(client):
    response = client.post(
        "/stock", json={"warehouse_code": "NOPE", "sku": "WIDGET-1", "quantity_on_hand": 10}
    )
    assert response.status_code == 404


def test_create_stock_item_returns_computed_available_quantity(client, warehouse):
    response = client.post(
        "/stock",
        json={"warehouse_code": warehouse, "sku": "WIDGET-1", "quantity_on_hand": 10, "reorder_threshold": 2},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["available_quantity"] == 10
    assert body["reserved_quantity"] == 0


def test_get_stock_filters_by_warehouse_and_sku(client, stock_item):
    warehouse_code, sku = stock_item
    response = client.get(f"/stock?warehouse_code={warehouse_code}&sku={sku}")
    body = response.get_json()
    assert len(body) == 1
    assert body[0]["sku"] == sku


def test_low_stock_endpoint_returns_items_at_or_below_threshold(client, warehouse):
    client.post(
        "/stock",
        json={"warehouse_code": warehouse, "sku": "LOW-1", "quantity_on_hand": 2, "reorder_threshold": 5},
    )
    client.post(
        "/stock",
        json={"warehouse_code": warehouse, "sku": "HEALTHY-1", "quantity_on_hand": 50, "reorder_threshold": 5},
    )

    response = client.get(f"/inventory/low-stock?warehouse_code={warehouse}")
    body = response.get_json()
    assert [item["sku"] for item in body] == ["LOW-1"]
