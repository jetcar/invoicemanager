"""Auto-generated from specs/invoice-service/v1/openapi.json. DO NOT EDIT MANUALLY."""

from __future__ import annotations

from typing import Any, TypedDict

class AutomationRuleCreate(TypedDict, total=False):
    account_code: Any | str
    confirmation_user_ids: Any | list[str]
    cost_center: Any | str
    description_pattern: Any | str
    priority: int
    supplier_name_pattern: Any | str

class AutomationRuleResponse(TypedDict, total=False):
    """Required fields in OpenAPI: account_code, company_id, confirmation_user_ids, cost_center, created_at, created_by, description_pattern, id, is_active, priority, supplier_name_pattern"""
    account_code: Any | str
    company_id: str
    confirmation_user_ids: Any | list[Any]
    cost_center: Any | str
    created_at: str
    created_by: str
    description_pattern: Any | str
    id: str
    is_active: bool
    priority: int
    supplier_name_pattern: Any | str

class Body_upload_einvoice_api_v1_invoices__company_id__upload_einvoice_post(TypedDict, total=False):
    """Required fields in OpenAPI: file"""
    file: str

class CommentCreate(TypedDict, total=False):
    """Required fields in OpenAPI: content"""
    content: str

class CommentResponse(TypedDict, total=False):
    """Required fields in OpenAPI: content, created_at, id, invoice_id, user_id"""
    content: str
    created_at: str
    id: str
    invoice_id: str
    user_id: str

class ConfirmationDecision(TypedDict, total=False):
    """Required fields in OpenAPI: approved"""
    approved: bool
    comment: Any | str

class ConfirmationStepCreate(TypedDict, total=False):
    """Required fields in OpenAPI: assigned_to, step_order"""
    assigned_to: str
    step_order: int

class ConfirmationStepResponse(TypedDict, total=False):
    """Required fields in OpenAPI: approved, assigned_to, comment, completed, completed_at, created_at, id, invoice_id, step_order"""
    approved: Any | bool
    assigned_to: str
    comment: Any | str
    completed: bool
    completed_at: Any | str
    created_at: str
    id: str
    invoice_id: str
    step_order: int

class HTTPValidationError(TypedDict, total=False):
    detail: list[ValidationError]

class InvoiceCreateRequest(TypedDict, total=False):
    """Required fields in OpenAPI: invoice_type"""
    currency: str
    customer_name: Any | str
    customer_reg_code: Any | str
    customer_vat_code: Any | str
    description: Any | str
    due_date: Any | str
    invoice_date: Any | str
    invoice_number: Any | str
    invoice_type: str
    lines: list[InvoiceLineCreate]
    net_amount: Any | float | str
    supplier_id: Any | str
    supplier_name: Any | str
    supplier_reg_code: Any | str
    supplier_vat_code: Any | str
    total_amount: Any | float | str
    vat_amount: Any | float | str

class InvoiceLineCreate(TypedDict, total=False):
    account_code: Any | str
    cost_center: Any | str
    description: Any | str
    line_number: int
    net_amount: Any | float | str
    quantity: Any | float | str
    total_amount: Any | float | str
    unit: Any | str
    unit_price: Any | float | str
    vat_amount: Any | float | str
    vat_rate: Any | float | str

class InvoiceLineResponse(TypedDict, total=False):
    """Required fields in OpenAPI: id, invoice_id"""
    account_code: Any | str
    cost_center: Any | str
    description: Any | str
    id: str
    invoice_id: str
    line_number: int
    net_amount: Any | str
    quantity: Any | str
    total_amount: Any | str
    unit: Any | str
    unit_price: Any | str
    vat_amount: Any | str
    vat_rate: Any | str

class InvoiceResponse(TypedDict, total=False):
    """Required fields in OpenAPI: assigned_to, company_id, created_at, created_by, currency, customer_name, customer_reg_code, customer_vat_code, description, due_date, id, invoice_date, invoice_number, invoice_type, net_amount, source, status, supplier_name, supplier_reg_code, supplier_vat_code, total_amount, updated_at, vat_amount"""
    assigned_to: Any | str
    company_id: str
    created_at: str
    created_by: str
    currency: str
    customer_name: Any | str
    customer_reg_code: Any | str
    customer_vat_code: Any | str
    description: Any | str
    due_date: Any | str
    id: str
    invoice_date: Any | str
    invoice_number: Any | str
    invoice_type: str
    lines: list[InvoiceLineResponse]
    net_amount: Any | str
    source: str
    status: str
    supplier_name: Any | str
    supplier_reg_code: Any | str
    supplier_vat_code: Any | str
    total_amount: Any | str
    updated_at: str
    vat_amount: Any | str

class InvoiceUpdateRequest(TypedDict, total=False):
    currency: Any | str
    customer_name: Any | str
    customer_reg_code: Any | str
    customer_vat_code: Any | str
    description: Any | str
    due_date: Any | str
    invoice_date: Any | str
    invoice_number: Any | str
    net_amount: Any | float | str
    status: Any | str
    supplier_name: Any | str
    supplier_reg_code: Any | str
    supplier_vat_code: Any | str
    total_amount: Any | float | str
    vat_amount: Any | float | str

class TransactionRowCreate(TypedDict, total=False):
    """Required fields in OpenAPI: amount"""
    account_code: Any | str
    amount: float | str
    cost_center: Any | str
    currency: str
    description: Any | str
    invoice_line_id: Any | str

class TransactionRowMergeRequest(TypedDict, total=False):
    """Required fields in OpenAPI: row_ids"""
    account_code: Any | str
    cost_center: Any | str
    description: Any | str
    row_ids: list[str]

class TransactionRowResponse(TypedDict, total=False):
    """Required fields in OpenAPI: account_code, amount, cost_center, created_at, created_by, currency, description, id, invoice_id, invoice_line_id, status, updated_at"""
    account_code: Any | str
    amount: str
    cost_center: Any | str
    created_at: str
    created_by: str
    currency: str
    description: Any | str
    id: str
    invoice_id: str
    invoice_line_id: Any | str
    status: str
    updated_at: str

class TransactionRowSplit(TypedDict, total=False):
    """Required fields in OpenAPI: amounts"""
    account_codes: Any | list[Any | str]
    amounts: list[float | str]
    cost_centers: Any | list[Any | str]
    descriptions: Any | list[Any | str]

class TransactionRowUpdate(TypedDict, total=False):
    account_code: Any | str
    amount: Any | float | str
    cost_center: Any | str
    currency: Any | str
    description: Any | str

class ValidationError(TypedDict, total=False):
    """Required fields in OpenAPI: loc, msg, type"""
    loc: list[int | str]
    msg: str
    type: str
