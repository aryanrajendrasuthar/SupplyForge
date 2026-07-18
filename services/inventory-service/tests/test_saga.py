from app.saga import handle_order_created


class FakeEventPublisher:
    def __init__(self):
        self.events: list[tuple[str, dict, str]] = []

    def publish(self, event_type, payload, correlation_id) -> None:
        self.events.append((event_type, payload, correlation_id))


def test_handle_order_created_reserves_all_line_items(app, stock_item):
    warehouse_code, sku = stock_item
    with app.app_context():
        db = app.session_factory()
        publisher = FakeEventPublisher()
        event = {"order_id": 1, "line_items": [{"sku": sku, "warehouse_code": warehouse_code, "quantity": 4}]}
        handle_order_created(db, publisher, event, correlation_id="corr-1")

        assert len(publisher.events) == 1
        event_type, payload, _ = publisher.events[0]
        assert event_type == "inventory.reserved"
        assert payload["order_id"] == 1
        assert len(payload["reservation_ids"]) == 1


def test_handle_order_created_publishes_failure_when_stock_insufficient(app, stock_item):
    warehouse_code, sku = stock_item
    with app.app_context():
        db = app.session_factory()
        publisher = FakeEventPublisher()
        event = {"order_id": 2, "line_items": [{"sku": sku, "warehouse_code": warehouse_code, "quantity": 999}]}
        handle_order_created(db, publisher, event, correlation_id="corr-2")

        assert len(publisher.events) == 1
        event_type, payload, _ = publisher.events[0]
        assert event_type == "inventory.reservation_failed"
        assert payload["order_id"] == 2
        assert "reason" in payload


def test_partial_failure_releases_earlier_reservations_in_the_batch(app, client, warehouse):
    client.post(
        "/stock", json={"warehouse_code": warehouse, "sku": "GOOD-1", "quantity_on_hand": 10, "reorder_threshold": 0}
    )
    client.post(
        "/stock", json={"warehouse_code": warehouse, "sku": "SCARCE-1", "quantity_on_hand": 1, "reorder_threshold": 0}
    )

    with app.app_context():
        db = app.session_factory()
        publisher = FakeEventPublisher()
        event = {
            "order_id": 3,
            "line_items": [
                {"sku": "GOOD-1", "warehouse_code": warehouse, "quantity": 5},
                {"sku": "SCARCE-1", "warehouse_code": warehouse, "quantity": 5},
            ],
        }
        handle_order_created(db, publisher, event, correlation_id="corr-3")

    event_type, _payload, _ = publisher.events[0]
    assert event_type == "inventory.reservation_failed"

    good_stock = client.get(f"/stock?warehouse_code={warehouse}&sku=GOOD-1").get_json()[0]
    assert good_stock["reserved_quantity"] == 0  # the earlier successful reservation was released
