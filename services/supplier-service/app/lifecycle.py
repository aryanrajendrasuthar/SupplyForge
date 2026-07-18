from sqlalchemy.orm import Session

from app.models import Supplier, SupplierAuditEntry, SupplierDocument


class InvalidTransitionError(Exception):
    pass


class MissingDocumentsError(Exception):
    pass


def _transition(db: Session, supplier: Supplier, new_status: str, actor: str, reason: str | None = None) -> None:
    db.add(
        SupplierAuditEntry(
            supplier_id=supplier.id,
            previous_status=supplier.status,
            new_status=new_status,
            actor=actor,
            reason=reason,
        )
    )
    supplier.status = new_status
    db.commit()


def register_supplier(db: Session, legal_name: str, contact_email: str, contact_phone: str | None) -> Supplier:
    supplier = Supplier(
        legal_name=legal_name, contact_email=contact_email, contact_phone=contact_phone, status="registered"
    )
    db.add(supplier)
    db.flush()  # assigns supplier.id before the audit entry references it

    db.add(
        SupplierAuditEntry(
            supplier_id=supplier.id,
            previous_status=None,
            new_status="registered",
            actor=contact_email,
            reason="initial registration",
        )
    )
    db.commit()
    db.refresh(supplier)
    return supplier


def add_document(db: Session, supplier: Supplier, document_type: str, filename: str, content: bytes) -> SupplierDocument:
    document = SupplierDocument(
        supplier_id=supplier.id, document_type=document_type, filename=filename, content=content
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def submit_for_review(db: Session, supplier: Supplier, actor: str) -> None:
    if supplier.status != "registered":
        raise InvalidTransitionError(f"cannot submit for review from status '{supplier.status}'")
    if not supplier.documents:
        raise MissingDocumentsError("at least one document must be uploaded before submitting for review")
    _transition(db, supplier, "under_review", actor)


def approve(db: Session, supplier: Supplier, approved_by: str) -> None:
    if supplier.status != "under_review":
        raise InvalidTransitionError(f"cannot approve from status '{supplier.status}'")
    _transition(db, supplier, "approved", approved_by)


def reject(db: Session, supplier: Supplier, rejected_by: str, reason: str) -> None:
    if supplier.status != "under_review":
        raise InvalidTransitionError(f"cannot reject from status '{supplier.status}'")
    _transition(db, supplier, "rejected", rejected_by, reason)


def deactivate(db: Session, supplier: Supplier, deactivated_by: str, reason: str) -> None:
    if supplier.status != "approved":
        raise InvalidTransitionError(f"cannot deactivate from status '{supplier.status}'")
    _transition(db, supplier, "deactivated", deactivated_by, reason)
