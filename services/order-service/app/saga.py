from sqlalchemy.orm import Session

from app.events import EventPublisher
from app.models import Order, OrderLineItem
from app.schemas import LineItemIn


def create_order(
    db: Session,
    publisher: EventPublisher,
    customer_email: str,
    line_items: list[LineItemIn],
    correlation_id: str,
) -> Order:
    order = Order(customer_email=customer_email, status="pending", correlation_id=correlation_id)
    order.line_items = [
        OrderLineItem(sku=item.sku, warehouse_code=item.warehouse_code, quantity=item.quantity)
        for item in line_items
    ]
    db.add(order)
    db.commit()
    db.refresh(order)

    publisher.publish(
        "order.created",
        {
            "order_id": order.id,
            "line_items": [
                {"sku": li.sku, "warehouse_code": li.warehouse_code, "quantity": li.quantity}
                for li in order.line_items
            ],
        },
        correlation_id,
    )
    return order


def handle_reservation_result(db: Session, event: dict) -> None:
    """Applies an inventory.reserved / inventory.reservation_failed event to its order.

    Guards on status=="pending" so a duplicate or late-arriving message (SQS is
    at-least-once delivery) can't re-apply a transition to an order that's
    already been resolved.
    """
    order = db.get(Order, event["order_id"])
    if order is None or order.status != "pending":
        return

    if event["event"] == "inventory.reserved":
        order.status = "confirmed"
    elif event["event"] == "inventory.reservation_failed":
        order.status = "cancelled"
        order.cancellation_reason = event.get("reason")
    db.commit()
