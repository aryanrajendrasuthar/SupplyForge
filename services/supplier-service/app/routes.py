from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from sqlalchemy import select

from app.lifecycle import (
    InvalidTransitionError,
    MissingDocumentsError,
    add_document,
    approve,
    deactivate,
    register_supplier,
    reject,
    submit_for_review,
)
from app.models import Supplier
from app.schemas import SupplierApprove, SupplierDeactivate, SupplierReject, SupplierRegister

bp = Blueprint("suppliers", __name__, url_prefix="/suppliers")


def _supplier_out(supplier: Supplier) -> dict:
    return {
        "id": supplier.id,
        "legal_name": supplier.legal_name,
        "contact_email": supplier.contact_email,
        "contact_phone": supplier.contact_phone,
        "status": supplier.status,
    }


def _get_supplier(supplier_id: int) -> Supplier | None:
    return g.db.get(Supplier, supplier_id)


@bp.post("")
def register():
    try:
        payload = SupplierRegister.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400

    supplier = register_supplier(g.db, payload.legal_name, payload.contact_email, payload.contact_phone)
    return jsonify(_supplier_out(supplier)), 201


@bp.get("")
def list_suppliers():
    status = request.args.get("status")
    stmt = select(Supplier).order_by(Supplier.id)
    if status:
        stmt = stmt.where(Supplier.status == status)
    suppliers = g.db.execute(stmt).scalars().all()
    return jsonify([_supplier_out(s) for s in suppliers])


@bp.get("/<int:supplier_id>")
def get_supplier(supplier_id: int):
    supplier = _get_supplier(supplier_id)
    if supplier is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(_supplier_out(supplier))


@bp.post("/<int:supplier_id>/documents")
def upload_document(supplier_id: int):
    supplier = _get_supplier(supplier_id)
    if supplier is None:
        return jsonify({"error": "not found"}), 404

    file = request.files.get("file")
    document_type = request.form.get("document_type")
    if file is None or not document_type:
        return jsonify({"error": "file and document_type are required"}), 400

    document = add_document(g.db, supplier, document_type, file.filename or "upload", file.read())
    return (
        jsonify({"id": document.id, "document_type": document.document_type, "filename": document.filename}),
        201,
    )


@bp.get("/<int:supplier_id>/documents")
def list_documents(supplier_id: int):
    supplier = _get_supplier(supplier_id)
    if supplier is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(
        [{"id": d.id, "document_type": d.document_type, "filename": d.filename} for d in supplier.documents]
    )


@bp.post("/<int:supplier_id>/submit-for-review")
def submit(supplier_id: int):
    supplier = _get_supplier(supplier_id)
    if supplier is None:
        return jsonify({"error": "not found"}), 404
    try:
        submit_for_review(g.db, supplier, actor=supplier.contact_email)
    except MissingDocumentsError as exc:
        return jsonify({"error": str(exc)}), 400
    except InvalidTransitionError as exc:
        return jsonify({"error": str(exc)}), 409
    return jsonify(_supplier_out(supplier))


@bp.post("/<int:supplier_id>/approve")
def approve_supplier(supplier_id: int):
    supplier = _get_supplier(supplier_id)
    if supplier is None:
        return jsonify({"error": "not found"}), 404
    try:
        payload = SupplierApprove.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400
    try:
        approve(g.db, supplier, payload.approved_by)
    except InvalidTransitionError as exc:
        return jsonify({"error": str(exc)}), 409
    return jsonify(_supplier_out(supplier))


@bp.post("/<int:supplier_id>/reject")
def reject_supplier(supplier_id: int):
    supplier = _get_supplier(supplier_id)
    if supplier is None:
        return jsonify({"error": "not found"}), 404
    try:
        payload = SupplierReject.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400
    try:
        reject(g.db, supplier, payload.rejected_by, payload.reason)
    except InvalidTransitionError as exc:
        return jsonify({"error": str(exc)}), 409
    return jsonify(_supplier_out(supplier))


@bp.post("/<int:supplier_id>/deactivate")
def deactivate_supplier(supplier_id: int):
    supplier = _get_supplier(supplier_id)
    if supplier is None:
        return jsonify({"error": "not found"}), 404
    try:
        payload = SupplierDeactivate.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"errors": exc.errors()}), 400
    try:
        deactivate(g.db, supplier, payload.deactivated_by, payload.reason)
    except InvalidTransitionError as exc:
        return jsonify({"error": str(exc)}), 409
    return jsonify(_supplier_out(supplier))


@bp.get("/<int:supplier_id>/audit-log")
def audit_log(supplier_id: int):
    supplier = _get_supplier(supplier_id)
    if supplier is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(
        [
            {
                "previous_status": e.previous_status,
                "new_status": e.new_status,
                "actor": e.actor,
                "reason": e.reason,
                "created_at": e.created_at.isoformat(),
            }
            for e in supplier.audit_entries
        ]
    )
