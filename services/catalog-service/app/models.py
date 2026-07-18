from datetime import datetime, timezone

from sqlalchemy import JSON, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Sku(Base):
    __tablename__ = "skus"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    category: Mapped[str] = mapped_column(String(128), index=True)
    compliance_certs: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow)

    pricing_tiers: Mapped[list["PricingTier"]] = relationship(
        back_populates="sku_ref", cascade="all, delete-orphan", order_by="PricingTier.min_quantity"
    )


class PricingTier(Base):
    __tablename__ = "pricing_tiers"
    __table_args__ = (UniqueConstraint("sku_id", "min_quantity", name="uq_pricing_tier_sku_qty"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sku_id: Mapped[int] = mapped_column(ForeignKey("skus.id"))
    min_quantity: Mapped[int]
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2))

    sku_ref: Mapped["Sku"] = relationship(back_populates="pricing_tiers")
