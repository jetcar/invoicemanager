import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ArchiveRequest(BaseModel):
    invoice_id: uuid.UUID
    company_id: uuid.UUID


class ArchivedInvoiceResponse(BaseModel):
    id: uuid.UUID
    original_id: uuid.UUID
    company_id: uuid.UUID
    invoice_type: str
    invoice_number: Optional[str]
    invoice_data: dict
    archived_at: datetime
    original_created_at: datetime

    model_config = {"from_attributes": True}
