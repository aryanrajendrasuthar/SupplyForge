from app.saga import handle_reservation_result


def _create_confirmed_order(client, notifier, app):
    response = client.post(
        "/orders",
        json={
            "customer_email": "customer@example.com",
            "line_items": [{"sku": "WIDGET-1", "warehouse_code": "WH1", "quantity": 2}],
        },
    )
    order_id = response.get_json()["id"]
    with app.app_context():
        db = app.session_factory()
        handle_reservation_result(db, notifier, {"event": "inventory.reserved", "order_id": order_id})
    return order_id


def test_cannot_ship_before_confirmed(client):
    response = client.post(
        "/orders", json={"customer_email": "c@example.com", "line_items": [{"sku": "W", "warehouse_code": "WH1", "quantity": 1}]}
    )
    order_id = response.get_json()["id"]
    assert client.post(f"/orders/{order_id}/ship").status_code == 409


def test_ship_requires_authentication(anon_client, app, client, notifier):
    order_id = _create_confirmed_order(client, notifier, app)
    assert anon_client.post(f"/orders/{order_id}/ship").status_code == 401


def test_ship_then_deliver_workflow(client, app, notifier):
    order_id = _create_confirmed_order(client, notifier, app)

    response = client.post(f"/orders/{order_id}/ship")
    assert response.status_code == 200
    assert response.get_json()["status"] == "shipped"
    assert notifier.sent[-1][1] == "Your order has shipped"

    response = client.post(f"/orders/{order_id}/deliver")
    assert response.status_code == 200
    assert response.get_json()["status"] == "delivered"
    assert notifier.sent[-1][1] == "Your order was delivered"


def test_cannot_deliver_before_shipped(client, app, notifier):
    order_id = _create_confirmed_order(client, notifier, app)
    assert client.post(f"/orders/{order_id}/deliver").status_code == 409


def test_ship_unknown_order_returns_404(client):
    assert client.post("/orders/9999/ship").status_code == 404
