from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PricingTierIn(BaseModel):
    min_quantity: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)


class PricingTierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    min_quantity: int
    unit_price: Decimal


class SkuCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category: str = Field(min_length=1, max_length=128)
    compliance_certs: list[str] = []
    image_url: str | None = Field(default=None, max_length=2048)
    technical_specs: dict[str, str] = {}
    pricing_tiers: list[PricingTierIn] = []


class SkuUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=128)
    compliance_certs: list[str] | None = None
    image_url: str | None = Field(default=None, max_length=2048)
    technical_specs: dict[str, str] | None = None
    pricing_tiers: list[PricingTierIn] | None = None
    is_active: bool | None = None


class SkuOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sku: str
    name: str
    description: str | None
    category: str
    compliance_certs: list[str]
    image_url: str | None
    technical_specs: dict[str, str]
    is_active: bool
    pricing_tiers: list[PricingTierOut]


class BulkImportRowResult(BaseModel):
    row: int
    sku: str | None = None
    status: str
    error: str | None = None


class BulkImportResult(BaseModel):
    created: int
    updated: int
    failed: int
    rows: list[BulkImportRowResult]
