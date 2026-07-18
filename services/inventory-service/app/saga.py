from sqlalchemy.orm import Session

from app.events import EventPublisher
from app.reservation_service import InsufficientStockError, NotFoundError, release_reservation, reserve_stock


def handle_order_created(db: Session, publisher: EventPublisher, event: dict, correlation_id: str) -> None:
    """Consumes an order.created event: reserves stock for every line item.

    If any line item can't be reserved, the reservations already made for
    this same order are released (the saga's compensating action) before
    publishing inventory.reservation_failed — an order should never end up
    partially reserved.
    """
    order_id = event["order_id"]
    line_items = event["line_items"]

    reservations = []
    try:
        for item in line_items:
            reservation = reserve_stock(
                db, item["warehouse_code"], item["sku"], item["quantity"], order_id=str(order_id)
            )
            reservations.append(reservation)
    except (NotFoundError, InsufficientStockError) as exc:
        for reservation in reservations:
            release_reservation(db, reservation)
        publisher.publish("inventory.reservation_failed", {"order_id": order_id, "reason": str(exc)}, correlation_id)
        return

    publisher.publish(
        "inventory.reserved",
        {"order_id": order_id, "reservation_ids": [r.id for r in reservations]},
        correlation_id,
    )
