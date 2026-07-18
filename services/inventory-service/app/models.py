from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))


class StockItem(Base):
    __tablename__ = "stock_items"
    __table_args__ = (UniqueConstraint("warehouse_id", "sku", name="uq_stock_item_warehouse_sku"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    sku: Mapped[str] = mapped_column(String(64), index=True)
    quantity_on_hand: Mapped[int] = mapped_column(default=0)
    reserved_quantity: Mapped[int] = mapped_column(default=0)
    reorder_threshold: Mapped[int] = mapped_column(default=0)

    warehouse: Mapped["Warehouse"] = relationship()

    @property
    def available_quantity(self) -> int:
        return self.quantity_on_hand - self.reserved_quantity


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id"))
    order_id: Mapped[str] = mapped_column(String(64), index=True)
    quantity: Mapped[int]
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | released | fulfilled
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    stock_item: Mapped["StockItem"] = relationship()
