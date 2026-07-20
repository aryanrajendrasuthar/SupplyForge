from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from supplyforge_auth import require_session

from app.models import Reservation, StockItem, Warehouse
from app.reservation_service import (
    InsufficientStockError,
    InvalidReservationStateError,
    NotFoundError,
    fulfill_reservation,
    low_stock_items,
    release_reservation,
    reserve_stock,
)
from app.schemas import ReservationCreate, StockItemCreate, WarehouseCreate

bp = Blueprint("inventory", __name__)


@bp.post("/warehouses")
@require_session()
def create_warehouse():
    try:
        payload = WarehouseCreate.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400

    warehouse = Warehouse(code=payload.code, name=payload.name)
    g.db.add(warehouse)
    try:
        g.db.commit()
    except IntegrityError:
        g.db.rollback()
        return jsonify({"error": f"warehouse '{payload.code}' already exists"}), 409

    return jsonify({"code": warehouse.code, "name": warehouse.name}), 201


@bp.get("/warehouses")
def list_warehouses():
    warehouses = g.db.execute(select(Warehouse).order_by(Warehouse.code)).scalars().all()
    return jsonify([{"code": w.code, "name": w.name} for w in warehouses])


def _stock_item_out(item: StockItem) -> dict:
    return {
        "warehouse_code": item.warehouse.code,
        "sku": item.sku,
        "quantity_on_hand": item.quantity_on_hand,
        "reserved_quantity": item.reserved_quantity,
        "available_quantity": item.available_quantity,
        "reorder_threshold": item.reorder_threshold,
    }


@bp.post("/stock")
@require_session()
def create_stock_item():
    try:
        payload = StockItemCreate.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400

    warehouse = g.db.execute(
        select(Warehouse).where(Warehouse.code == payload.warehouse_code)
    ).scalar_one_or_none()
    if warehouse is None:
        return jsonify({"error": f"warehouse '{payload.warehouse_code}' not found"}), 404

    item = StockItem(
        warehouse_id=warehouse.id,
        sku=payload.sku,
        quantity_on_hand=payload.quantity_on_hand,
        reorder_threshold=payload.reorder_threshold,
    )
    g.db.add(item)
    try:
        g.db.commit()
    except IntegrityError:
        g.db.rollback()
        return (
            jsonify({"error": f"stock item for '{payload.sku}' already exists in '{payload.warehouse_code}'"}),
            409,
        )

    return jsonify(_stock_item_out(item)), 201


@bp.get("/stock")
def get_stock():
    warehouse_code = request.args.get("warehouse_code")
    sku = request.args.get("sku")

    stmt = select(StockItem).join(Warehouse)
    if warehouse_code:
        stmt = stmt.where(Warehouse.code == warehouse_code)
    if sku:
        stmt = stmt.where(StockItem.sku == sku)

    items = g.db.execute(stmt).scalars().all()
    return jsonify([_stock_item_out(i) for i in items])


def _reservation_out(reservation: Reservation) -> dict:
    return {
        "id": reservation.id,
        "warehouse_code": reservation.stock_item.warehouse.code,
        "sku": reservation.stock_item.sku,
        "quantity": reservation.quantity,
        "order_id": reservation.order_id,
        "status": reservation.status,
    }


# Reservation endpoints are saga-internal (see app/saga.py and
# order-service's consumer) rather than user-facing, so they're not
# session-gated the way warehouse/stock setup is — the caller here is
# always the order/inventory saga machinery, identified by which SQS
# messages it's reacting to, not a logged-in operator.
@bp.post("/reservations")
def create_reservation():
    try:
        payload = ReservationCreate.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400

    try:
        reservation = reserve_stock(
            g.db, payload.warehouse_code, payload.sku, payload.quantity, payload.order_id
        )
    except NotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except InsufficientStockError as exc:
        return jsonify({"error": str(exc)}), 409

    return jsonify(_reservation_out(reservation)), 201


@bp.post("/reservations/<int:reservation_id>/release")
def release(reservation_id: int):
    reservation = g.db.get(Reservation, reservation_id)
    if reservation is None:
        return jsonify({"error": "not found"}), 404
    try:
        release_reservation(g.db, reservation)
    except InvalidReservationStateError as exc:
        return jsonify({"error": str(exc)}), 409
    return jsonify(_reservation_out(reservation))


@bp.post("/reservations/<int:reservation_id>/fulfill")
def fulfill(reservation_id: int):
    reservation = g.db.get(Reservation, reservation_id)
    if reservation is None:
        return jsonify({"error": "not found"}), 404
    try:
        fulfill_reservation(g.db, reservation)
    except InvalidReservationStateError as exc:
        return jsonify({"error": str(exc)}), 409
    return jsonify(_reservation_out(reservation))


@bp.get("/inventory/low-stock")
def low_stock():
    warehouse_code = request.args.get("warehouse_code")
    items = low_stock_items(g.db, warehouse_code)
    return jsonify([_stock_item_out(i) for i in items])
