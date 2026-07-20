from pydantic import BaseModel, EmailStr, Field


class SupplierRegister(BaseModel):
    legal_name: str = Field(min_length=1, max_length=255)
    contact_email: EmailStr
    contact_phone: str | None = Field(default=None, max_length=32)


class SupplierReject(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class SupplierDeactivate(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=255)
    role: str = Field(default="analyst", pattern="^(analyst|approver|admin)$")


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = None
