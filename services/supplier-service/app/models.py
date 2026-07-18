from datetime import datetime, timezone

from sqlalchemy import ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    legal_name: Mapped[str] = mapped_column(String(255))
    contact_email: Mapped[str] = mapped_column(String(255), index=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="registered")
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow)

    documents: Mapped[list["SupplierDocument"]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
    audit_entries: Mapped[list["SupplierAuditEntry"]] = relationship(
        back_populates="supplier",
        cascade="all, delete-orphan",
        order_by="SupplierAuditEntry.created_at",
    )


class SupplierDocument(Base):
    __tablename__ = "supplier_documents"

    # Document bytes live in the DB for now (no Cloudflare R2 credentials in
    # local/CI dev — see docs/project-plan.md §1). Swapping the `content`
    # column for an R2 object key is a follow-up once those creds exist.
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    document_type: Mapped[str] = mapped_column(String(64))
    filename: Mapped[str] = mapped_column(String(255))
    content: Mapped[bytes] = mapped_column(LargeBinary)
    uploaded_at: Mapped[datetime] = mapped_column(default=_utcnow)

    supplier: Mapped["Supplier"] = relationship(back_populates="documents")


class SupplierAuditEntry(Base):
    __tablename__ = "supplier_audit_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    previous_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str] = mapped_column(String(32))
    actor: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    supplier: Mapped["Supplier"] = relationship(back_populates="audit_entries")
