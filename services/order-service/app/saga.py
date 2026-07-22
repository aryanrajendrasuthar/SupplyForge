from sqlalchemy.orm import Session

from app.events import EventPublisher
from app.models import Order, OrderLineItem
from app.notifications import Notifier
from app.schemas import LineItemIn


class InvalidTransitionError(Exception):
    pass


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


def handle_reservation_result(db: Session, notifier: Notifier, event: dict) -> None:
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
        db.commit()
        notifier.send(
            order.customer_email, "Order confirmed", f"Your order #{order.id} has been confirmed."
        )
    elif event["event"] == "inventory.reservation_failed":
        order.status = "cancelled"
        order.cancellation_reason = event.get("reason")
        db.commit()
        notifier.send(
            order.customer_email,
            "Order cancelled",
            f"Your order #{order.id} could not be fulfilled: {event.get('reason')}",
        )


def ship_order(db: Session, notifier: Notifier, order: Order) -> None:
    if order.status != "confirmed":
        raise InvalidTransitionError(f"cannot ship from status '{order.status}'")
    order.status = "shipped"
    db.commit()
    notifier.send(order.customer_email, "Your order has shipped", f"Order #{order.id} is on its way.")


def deliver_order(db: Session, notifier: Notifier, order: Order) -> None:
    if order.status != "shipped":
        raise InvalidTransitionError(f"cannot deliver from status '{order.status}'")
    order.status = "delivered"
    db.commit()
    notifier.send(
        order.customer_email, "Your order was delivered", f"Order #{order.id} has been delivered."
    )
