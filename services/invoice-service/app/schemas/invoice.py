import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Invoice Line
# ──────────────────────────────────────────────
class InvoiceLineCreate(BaseModel):
    line_number: int = 1
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    account_code: Optional[str] = None
    cost_center: Optional[str] = None


class InvoiceLineResponse(InvoiceLineCreate):
    id: uuid.UUID
    invoice_id: uuid.UUID

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Invoice
# ──────────────────────────────────────────────
class InvoiceCreateRequest(BaseModel):
    invoice_type: str  # "purchase" | "sales"
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    supplier_id: Optional[uuid.UUID] = None
    supplier_name: Optional[str] = None
    supplier_reg_code: Optional[str] = None
    supplier_vat_code: Optional[str] = None
    customer_name: Optional[str] = None
    customer_reg_code: Optional[str] = None
    customer_vat_code: Optional[str] = None
    currency: str = "EUR"
    net_amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    description: Optional[str] = None
    lines: List[InvoiceLineCreate] = []


class InvoiceUpdateRequest(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    supplier_name: Optional[str] = None
    supplier_reg_code: Optional[str] = None
    supplier_vat_code: Optional[str] = None
    customer_name: Optional[str] = None
    customer_reg_code: Optional[str] = None
    customer_vat_code: Optional[str] = None
    currency: Optional[str] = None
    net_amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    description: Optional[str] = None
    status: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    invoice_type: str
    status: str
    source: str
    invoice_number: Optional[str]
    invoice_date: Optional[date]
    due_date: Optional[date]
    supplier_name: Optional[str]
    supplier_reg_code: Optional[str]
    supplier_vat_code: Optional[str]
    customer_name: Optional[str]
    customer_reg_code: Optional[str]
    customer_vat_code: Optional[str]
    currency: str
    net_amount: Optional[Decimal]
    vat_amount: Optional[Decimal]
    total_amount: Optional[Decimal]
    description: Optional[str]
    assigned_to: Optional[uuid.UUID]
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Transaction rows
# ──────────────────────────────────────────────
class TransactionRowCreate(BaseModel):
    invoice_line_id: Optional[uuid.UUID] = None
    account_code: Optional[str] = None
    cost_center: Optional[str] = None
    description: Optional[str] = None
    amount: Decimal
    currency: str = "EUR"


class TransactionRowUpdate(BaseModel):
    account_code: Optional[str] = None
    cost_center: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None


class TransactionRowResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    invoice_line_id: Optional[uuid.UUID]
    status: str
    account_code: Optional[str]
    cost_center: Optional[str]
    description: Optional[str]
    amount: Decimal
    currency: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionRowSplit(BaseModel):
    """Split a transaction row into two or more rows with given amounts."""
    amounts: List[Decimal] = Field(min_length=2)
    descriptions: Optional[List[Optional[str]]] = None
    account_codes: Optional[List[Optional[str]]] = None
    cost_centers: Optional[List[Optional[str]]] = None


class TransactionRowMergeRequest(BaseModel):
    """Merge multiple transaction rows into one."""
    row_ids: List[uuid.UUID] = Field(min_length=2)
    account_code: Optional[str] = None
    cost_center: Optional[str] = None
    description: Optional[str] = None


# ──────────────────────────────────────────────
# Confirmation
# ──────────────────────────────────────────────
class ConfirmationStepCreate(BaseModel):
    assigned_to: uuid.UUID
    step_order: int


class ConfirmationStepResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    step_order: int
    assigned_to: uuid.UUID
    completed: bool
    approved: Optional[bool]
    comment: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ConfirmationDecision(BaseModel):
    approved: bool
    comment: Optional[str] = None


# ──────────────────────────────────────────────
# Comments
# ──────────────────────────────────────────────
class CommentCreate(BaseModel):
    content: str = Field(min_length=1)


class CommentResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Automation rules
# ──────────────────────────────────────────────
class AutomationRuleCreate(BaseModel):
    supplier_name_pattern: Optional[str] = None
    description_pattern: Optional[str] = None
    account_code: Optional[str] = None
    cost_center: Optional[str] = None
    confirmation_user_ids: Optional[List[uuid.UUID]] = None
    priority: int = 0


class AutomationRuleResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    supplier_name_pattern: Optional[str]
    description_pattern: Optional[str]
    account_code: Optional[str]
    cost_center: Optional[str]
    confirmation_user_ids: Optional[list]
    priority: int
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
