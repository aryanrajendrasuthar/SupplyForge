from pydantic import BaseModel, Field


class WarehouseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)


class StockItemCreate(BaseModel):
    warehouse_code: str = Field(min_length=1, max_length=32)
    sku: str = Field(min_length=1, max_length=64)
    quantity_on_hand: int = Field(ge=0)
    reorder_threshold: int = Field(ge=0, default=0)


class ReservationCreate(BaseModel):
    warehouse_code: str = Field(min_length=1, max_length=32)
    sku: str = Field(min_length=1, max_length=64)
    quantity: int = Field(gt=0)
    order_id: str = Field(min_length=1, max_length=64)
