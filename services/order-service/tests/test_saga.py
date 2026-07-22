from app.saga import handle_reservation_result


def _create_order(client):
    response = client.post(
        "/orders",
        json={
            "customer_email": "customer@example.com",
            "line_items": [{"sku": "WIDGET-1", "warehouse_code": "WH1", "quantity": 2}],
        },
    )
    return response.get_json()["id"]


def test_reservation_success_confirms_order(app, client, notifier):
    order_id = _create_order(client)
    with app.app_context():
        db = app.session_factory()
        handle_reservation_result(db, notifier, {"event": "inventory.reserved", "order_id": order_id})

    body = client.get(f"/orders/{order_id}").get_json()
    assert body["status"] == "confirmed"
    assert notifier.sent[-1][0] == "customer@example.com"
    assert notifier.sent[-1][1] == "Order confirmed"


def test_reservation_failure_cancels_order_with_reason(app, client, notifier):
    order_id = _create_order(client)
    with app.app_context():
        db = app.session_factory()
        handle_reservation_result(
            db,
            notifier,
            {
                "event": "inventory.reservation_failed",
                "order_id": order_id,
                "reason": "requested 2, only 1 available",
            },
        )

    body = client.get(f"/orders/{order_id}").get_json()
    assert body["status"] == "cancelled"
    assert body["cancellation_reason"] == "requested 2, only 1 available"
    assert notifier.sent[-1][1] == "Order cancelled"


def test_duplicate_reservation_event_is_ignored_once_resolved(app, client, notifier):
    order_id = _create_order(client)
    with app.app_context():
        db = app.session_factory()
        handle_reservation_result(db, notifier, {"event": "inventory.reserved", "order_id": order_id})
        # A second, late-arriving message for the same order must not flip a
        # resolved order back — SQS is at-least-once delivery.
        handle_reservation_result(
            db,
            notifier,
            {"event": "inventory.reservation_failed", "order_id": order_id, "reason": "late duplicate"},
        )

    body = client.get(f"/orders/{order_id}").get_json()
    assert body["status"] == "confirmed"


def test_event_for_unknown_order_is_ignored(app, notifier):
    with app.app_context():
        db = app.session_factory()
        handle_reservation_result(db, notifier, {"event": "inventory.reserved", "order_id": 9999})  # should not raise
