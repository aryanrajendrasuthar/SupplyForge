from pydantic import BaseModel, EmailStr, Field


class LineItemIn(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    warehouse_code: str = Field(min_length=1, max_length=32)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    customer_email: EmailStr
    line_items: list[LineItemIn] = Field(min_length=1)
