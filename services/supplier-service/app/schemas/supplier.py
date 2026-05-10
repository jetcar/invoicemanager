import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    reg_code: Optional[str] = None
    vat_code: Optional[str] = None
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    iban: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    reg_code: Optional[str] = None
    vat_code: Optional[str] = None
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    iban: Optional[str] = None


class SupplierResponse(BaseModel):
    id: uuid.UUID
    company_id: Optional[uuid.UUID]
    name: str
    reg_code: Optional[str]
    vat_code: Optional[str]
    address: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    iban: Optional[str]
    is_shared: bool
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
