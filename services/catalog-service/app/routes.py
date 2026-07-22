from flask import Blueprint, current_app, g, jsonify, request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from supplyforge_auth import require_session

from app.bulk_import import parse_bulk_import
from app.models import PricingTier, Sku
from app.schemas import SkuCreate, SkuOut, SkuUpdate

bp = Blueprint("skus", __name__, url_prefix="/skus")


def _sku_to_out(sku: Sku) -> dict:
    return SkuOut.model_validate(sku).model_dump(mode="json")


def _get_sku(db, sku_code: str) -> Sku | None:
    return db.execute(select(Sku).where(Sku.sku == sku_code)).scalar_one_or_none()


@bp.post("")
@require_session()
def create_sku():
    try:
        payload = SkuCreate.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400

    db = g.db
    sku = Sku(
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        compliance_certs=payload.compliance_certs,
        image_url=payload.image_url,
        technical_specs=payload.technical_specs,
        pricing_tiers=[
            PricingTier(min_quantity=t.min_quantity, unit_price=t.unit_price) for t in payload.pricing_tiers
        ],
    )
    db.add(sku)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return jsonify({"error": f"SKU '{payload.sku}' already exists"}), 409

    return jsonify(_sku_to_out(sku)), 201


@bp.get("")
def list_skus():
    db = g.db
    category = request.args.get("category")
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("page_size", 25)), 1), 100)

    stmt = select(Sku).where(Sku.is_active)
    if category:
        stmt = stmt.where(Sku.category == category)
    stmt = stmt.order_by(Sku.sku).offset((page - 1) * page_size).limit(page_size)

    skus = db.execute(stmt).scalars().all()
    return jsonify({"items": [_sku_to_out(s) for s in skus], "page": page, "page_size": page_size})


@bp.get("/<sku_code>")
def get_sku(sku_code: str):
    sku = _get_sku(g.db, sku_code)
    if sku is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(_sku_to_out(sku))


@bp.patch("/<sku_code>")
@require_session()
def update_sku(sku_code: str):
    try:
        payload = SkuUpdate.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400

    db = g.db
    sku = _get_sku(db, sku_code)
    if sku is None:
        return jsonify({"error": "not found"}), 404

    updates = payload.model_dump(exclude_unset=True, exclude={"pricing_tiers"})
    for field, value in updates.items():
        setattr(sku, field, value)

    price_changed = payload.pricing_tiers is not None
    if price_changed:
        # Flush the deletes before inserting the replacement rows, otherwise the
        # (sku_id, min_quantity) unique constraint can collide with the old rows
        # that haven't been physically removed yet within the same flush.
        sku.pricing_tiers.clear()
        db.flush()
        sku.pricing_tiers.extend(
            PricingTier(min_quantity=t.min_quantity, unit_price=t.unit_price) for t in payload.pricing_tiers
        )

    db.commit()

    if price_changed:
        current_app.event_publisher.publish("pricing.updated", {"sku": sku.sku}, g.get("correlation_id", ""))

    return jsonify(_sku_to_out(sku))


@bp.delete("/<sku_code>")
@require_session()
def deactivate_sku(sku_code: str):
    db = g.db
    sku = _get_sku(db, sku_code)
    if sku is None:
        return jsonify({"error": "not found"}), 404
    sku.is_active = False
    db.commit()
    return "", 204


@bp.post("/bulk-import")
@require_session()
def bulk_import():
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "no file uploaded"}), 400

    result = parse_bulk_import(file.filename or "", file.read(), g.db)
    return jsonify(result.model_dump()), 200
