import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuditLogCreate(BaseModel):
    user_id: Optional[uuid.UUID] = None
    company_id: Optional[uuid.UUID] = None
    service: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    extra_data: Optional[dict] = None


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    company_id: Optional[uuid.UUID]
    service: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: Optional[str]
    extra_data: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}
