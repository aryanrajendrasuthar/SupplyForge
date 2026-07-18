from pydantic import BaseModel, EmailStr, Field


class SupplierRegister(BaseModel):
    legal_name: str = Field(min_length=1, max_length=255)
    contact_email: EmailStr
    contact_phone: str | None = Field(default=None, max_length=32)


class SupplierApprove(BaseModel):
    # No session/role system wired into services yet (that arrives in Phase 6
    # security hardening); until then the approver identity is passed
    # explicitly rather than derived from a session.
    approved_by: EmailStr


class SupplierReject(BaseModel):
    rejected_by: EmailStr
    reason: str = Field(min_length=1, max_length=1000)


class SupplierDeactivate(BaseModel):
    deactivated_by: EmailStr
    reason: str = Field(min_length=1, max_length=1000)
