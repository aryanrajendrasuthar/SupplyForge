def test_reserve_stock_succeeds_and_reduces_availability(client, stock_item):
    warehouse_code, sku = stock_item
    response = client.post(
        "/reservations",
        json={"warehouse_code": warehouse_code, "sku": sku, "quantity": 4, "order_id": "order-1"},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "active"
    assert body["quantity"] == 4

    stock = client.get(f"/stock?warehouse_code={warehouse_code}&sku={sku}").get_json()[0]
    assert stock["reserved_quantity"] == 4
    assert stock["available_quantity"] == 6


def test_reserve_stock_rejects_when_insufficient(client, stock_item):
    warehouse_code, sku = stock_item
    response = client.post(
        "/reservations",
        json={"warehouse_code": warehouse_code, "sku": sku, "quantity": 999, "order_id": "order-1"},
    )
    assert response.status_code == 409


def test_reserve_stock_404_for_unknown_sku(client, warehouse):
    response = client.post(
        "/reservations",
        json={"warehouse_code": warehouse, "sku": "NOPE", "quantity": 1, "order_id": "order-1"},
    )
    assert response.status_code == 404


def test_release_reservation_restores_availability(client, stock_item):
    warehouse_code, sku = stock_item
    reservation = client.post(
        "/reservations",
        json={"warehouse_code": warehouse_code, "sku": sku, "quantity": 4, "order_id": "order-1"},
    ).get_json()

    response = client.post(f"/reservations/{reservation['id']}/release")
    assert response.status_code == 200
    assert response.get_json()["status"] == "released"

    stock = client.get(f"/stock?warehouse_code={warehouse_code}&sku={sku}").get_json()[0]
    assert stock["reserved_quantity"] == 0
    assert stock["available_quantity"] == 10


def test_fulfill_reservation_reduces_quantity_on_hand(client, stock_item):
    warehouse_code, sku = stock_item
    reservation = client.post(
        "/reservations",
        json={"warehouse_code": warehouse_code, "sku": sku, "quantity": 4, "order_id": "order-1"},
    ).get_json()

    response = client.post(f"/reservations/{reservation['id']}/fulfill")
    assert response.status_code == 200
    assert response.get_json()["status"] == "fulfilled"

    stock = client.get(f"/stock?warehouse_code={warehouse_code}&sku={sku}").get_json()[0]
    assert stock["quantity_on_hand"] == 6
    assert stock["reserved_quantity"] == 0
    assert stock["available_quantity"] == 6


def test_cannot_release_an_already_fulfilled_reservation(client, stock_item):
    warehouse_code, sku = stock_item
    reservation = client.post(
        "/reservations",
        json={"warehouse_code": warehouse_code, "sku": sku, "quantity": 4, "order_id": "order-1"},
    ).get_json()
    client.post(f"/reservations/{reservation['id']}/fulfill")

    response = client.post(f"/reservations/{reservation['id']}/release")
    assert response.status_code == 409


def test_release_of_unknown_reservation_404s(client):
    response = client.post("/reservations/9999/release")
    assert response.status_code == 404


def test_correlation_id_is_echoed_back(client):
    response = client.get("/warehouses", headers={"X-Correlation-ID": "test-corr-id"})
    assert response.headers["X-Correlation-ID"] == "test-corr-id"
