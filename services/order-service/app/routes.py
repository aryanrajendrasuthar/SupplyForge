from flask import Blueprint, current_app, g, jsonify, request
from pydantic import ValidationError
from sqlalchemy import select
from supplyforge_auth import require_session

from app.models import Order
from app.saga import create_order
from app.schemas import OrderCreate

bp = Blueprint("orders", __name__, url_prefix="/orders")


def _order_out(order: Order) -> dict:
    return {
        "id": order.id,
        "customer_email": order.customer_email,
        "status": order.status,
        "cancellation_reason": order.cancellation_reason,
        "line_items": [
            {"sku": li.sku, "warehouse_code": li.warehouse_code, "quantity": li.quantity}
            for li in order.line_items
        ],
    }


@bp.post("")
@require_session()
def create():
    try:
        payload = OrderCreate.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400

    order = create_order(
        g.db,
        current_app.event_publisher,
        payload.customer_email,
        payload.line_items,
        g.get("correlation_id", ""),
    )
    return jsonify(_order_out(order)), 201


@bp.get("/<int:order_id>")
def get_order(order_id: int):
    order = g.db.get(Order, order_id)
    if order is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(_order_out(order))


@bp.get("")
def list_orders():
    status = request.args.get("status")
    stmt = select(Order).order_by(Order.id)
    if status:
        stmt = stmt.where(Order.status == status)
    orders = g.db.execute(stmt).scalars().all()
    return jsonify([_order_out(o) for o in orders])
