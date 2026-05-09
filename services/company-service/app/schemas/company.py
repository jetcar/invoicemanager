import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class OrganizationMemberAdd(BaseModel):
    user_id: uuid.UUID
    role: str = "auditor"


class CompanyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    reg_code: Optional[str] = None
    vat_code: Optional[str] = None
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    iban: Optional[str] = None
    organization_id: Optional[uuid.UUID] = None


class CompanyUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    reg_code: Optional[str] = None
    vat_code: Optional[str] = None
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    iban: Optional[str] = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    reg_code: Optional[str]
    vat_code: Optional[str]
    address: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    iban: Optional[str]
    status: str
    api_key: Optional[str]
    organization_id: Optional[uuid.UUID]
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyMemberAdd(BaseModel):
    user_id: uuid.UUID
    role: str = "auditor"


class CompanyMemberResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    added_at: datetime

    model_config = {"from_attributes": True}
