from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Reservation, StockItem, Warehouse


class NotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class InvalidReservationStateError(Exception):
    pass


def get_stock_item(db: Session, warehouse_code: str, sku: str) -> StockItem | None:
    return db.execute(
        select(StockItem).join(Warehouse).where(Warehouse.code == warehouse_code, StockItem.sku == sku)
    ).scalar_one_or_none()


def reserve_stock(db: Session, warehouse_code: str, sku: str, quantity: int, order_id: str) -> Reservation:
    stock_item = get_stock_item(db, warehouse_code, sku)
    if stock_item is None:
        raise NotFoundError(f"no stock item for SKU '{sku}' in warehouse '{warehouse_code}'")

    if stock_item.available_quantity < quantity:
        raise InsufficientStockError(
            f"requested {quantity}, only {stock_item.available_quantity} available"
        )

    stock_item.reserved_quantity += quantity
    reservation = Reservation(
        stock_item_id=stock_item.id, order_id=order_id, quantity=quantity, status="active"
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def release_reservation(db: Session, reservation: Reservation) -> None:
    if reservation.status != "active":
        raise InvalidReservationStateError(f"cannot release a '{reservation.status}' reservation")
    reservation.stock_item.reserved_quantity -= reservation.quantity
    reservation.status = "released"
    db.commit()


def fulfill_reservation(db: Session, reservation: Reservation) -> None:
    if reservation.status != "active":
        raise InvalidReservationStateError(f"cannot fulfill a '{reservation.status}' reservation")
    reservation.stock_item.reserved_quantity -= reservation.quantity
    reservation.stock_item.quantity_on_hand -= reservation.quantity
    reservation.status = "fulfilled"
    db.commit()


def low_stock_items(db: Session, warehouse_code: str | None = None) -> list[StockItem]:
    stmt = select(StockItem).join(Warehouse)
    if warehouse_code:
        stmt = stmt.where(Warehouse.code == warehouse_code)
    items = db.execute(stmt).scalars().all()
    return [item for item in items if item.available_quantity <= item.reorder_threshold]
