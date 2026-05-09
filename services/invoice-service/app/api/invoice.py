import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.invoice import (
    Invoice,
    InvoiceLine,
    TransactionRow,
    ConfirmationStep,
    InvoiceComment,
    InvoiceAutomationRule,
    InvoiceType,
    InvoiceStatus,
    InvoiceSource,
    TransactionRowStatus,
)
from app.schemas.invoice import (
    InvoiceCreateRequest,
    InvoiceUpdateRequest,
    InvoiceResponse,
    InvoiceLineCreate,
    InvoiceLineResponse,
    TransactionRowCreate,
    TransactionRowUpdate,
    TransactionRowResponse,
    TransactionRowSplit,
    TransactionRowMergeRequest,
    ConfirmationStepCreate,
    ConfirmationStepResponse,
    ConfirmationDecision,
    CommentCreate,
    CommentResponse,
    AutomationRuleCreate,
    AutomationRuleResponse,
)
from app.services.einvoice_parser import parse_einvoice_xml
from app.services.automation import apply_automation_rules

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


# ──────────────────────────────────────────────
# Invoice CRUD
# ──────────────────────────────────────────────
@router.post("/{company_id}", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    company_id: uuid.UUID,
    payload: InvoiceCreateRequest,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = Invoice(
        company_id=company_id,
        invoice_type=InvoiceType(payload.invoice_type),
        source=InvoiceSource.MANUAL,
        status=InvoiceStatus.DRAFT,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        supplier_id=payload.supplier_id,
        supplier_name=payload.supplier_name,
        supplier_reg_code=payload.supplier_reg_code,
        supplier_vat_code=payload.supplier_vat_code,
        customer_name=payload.customer_name,
        customer_reg_code=payload.customer_reg_code,
        customer_vat_code=payload.customer_vat_code,
        currency=payload.currency,
        net_amount=payload.net_amount,
        vat_amount=payload.vat_amount,
        total_amount=payload.total_amount,
        description=payload.description,
        created_by=current_user_id,
    )
    db.add(invoice)
    await db.flush()

    for line_data in payload.lines:
        line = InvoiceLine(invoice_id=invoice.id, **line_data.model_dump())
        db.add(line)

    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.get("/{company_id}", response_model=list[InvoiceResponse])
async def list_invoices(
    company_id: uuid.UUID,
    invoice_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Invoice).where(Invoice.company_id == company_id)
    if invoice_type:
        query = query.where(Invoice.invoice_type == InvoiceType(invoice_type))
    if status_filter:
        query = query.where(Invoice.status == InvoiceStatus(status_filter))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{company_id}/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await _get_invoice(company_id, invoice_id, db)
    return invoice


@router.patch("/{company_id}/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    payload: InvoiceUpdateRequest,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await _get_invoice(company_id, invoice_id, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(invoice, field, value)
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.delete("/{company_id}/{invoice_id}")
async def delete_invoice(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await _get_invoice(company_id, invoice_id, db)
    await db.delete(invoice)
    await db.commit()
    return {"message": "Invoice deleted"}


# ──────────────────────────────────────────────
# E-invoice upload (purchase invoices)
# ──────────────────────────────────────────────
@router.post("/{company_id}/upload-einvoice", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def upload_einvoice(
    company_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    xml_bytes = await file.read()
    try:
        parsed = parse_einvoice_xml(xml_bytes)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid e-invoice XML: {exc}")

    source_map = {"einvoice_et": InvoiceSource.EINVOICE_ET, "ubl": InvoiceSource.UBL}
    source = source_map.get(parsed.pop("source", "einvoice_et"), InvoiceSource.EINVOICE_ET)
    lines_data = parsed.pop("lines", [])

    invoice = Invoice(
        company_id=company_id,
        invoice_type=InvoiceType.PURCHASE,
        source=source,
        status=InvoiceStatus.PENDING,
        raw_xml=xml_bytes.decode("utf-8", errors="replace"),
        created_by=current_user_id,
        **{k: v for k, v in parsed.items() if v is not None},
    )
    db.add(invoice)
    await db.flush()

    for ld in lines_data:
        line = InvoiceLine(invoice_id=invoice.id, **{k: v for k, v in ld.items() if v is not None})
        db.add(line)

    await db.flush()
    await db.refresh(invoice)

    # Apply automation rules
    await apply_automation_rules(invoice, current_user_id, db)
    await db.commit()
    await db.refresh(invoice)
    return invoice


# ──────────────────────────────────────────────
# Sales invoice API import (using company API key)
# ──────────────────────────────────────────────
@router.post("/api-import/{api_key}", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def api_import_invoice(
    api_key: str,
    payload: InvoiceCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import a sales invoice via company API key (no user authentication required)."""
    # In a real scenario, we'd look up the company by api_key via company-service
    # For now we expect the company_id in the payload's supplier/customer context
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="API import requires company lookup service integration",
    )


# ──────────────────────────────────────────────
# Transaction Rows
# ──────────────────────────────────────────────
@router.get("/{company_id}/{invoice_id}/transaction-rows", response_model=list[TransactionRowResponse])
async def list_transaction_rows(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_invoice(company_id, invoice_id, db)
    result = await db.execute(
        select(TransactionRow).where(TransactionRow.invoice_id == invoice_id)
    )
    return result.scalars().all()


@router.post("/{company_id}/{invoice_id}/transaction-rows", response_model=TransactionRowResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction_row(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    payload: TransactionRowCreate,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_invoice(company_id, invoice_id, db)
    row = TransactionRow(
        invoice_id=invoice_id,
        created_by=current_user_id,
        **payload.model_dump(),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/{company_id}/{invoice_id}/transaction-rows/{row_id}", response_model=TransactionRowResponse)
async def update_transaction_row(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    row_id: uuid.UUID,
    payload: TransactionRowUpdate,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await _get_transaction_row(invoice_id, row_id, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{company_id}/{invoice_id}/transaction-rows/{row_id}")
async def delete_transaction_row(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    row_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await _get_transaction_row(invoice_id, row_id, db)
    await db.delete(row)
    await db.commit()
    return {"message": "Transaction row deleted"}


@router.post("/{company_id}/{invoice_id}/transaction-rows/{row_id}/split", response_model=list[TransactionRowResponse])
async def split_transaction_row(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    row_id: uuid.UUID,
    payload: TransactionRowSplit,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await _get_transaction_row(invoice_id, row_id, db)
    total = sum(payload.amounts)
    if abs(total - row.amount) > Decimal("0.01"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Split amounts ({total}) must sum to row amount ({row.amount})",
        )

    new_rows = []
    for i, amount in enumerate(payload.amounts):
        new_row = TransactionRow(
            invoice_id=invoice_id,
            invoice_line_id=row.invoice_line_id,
            account_code=(payload.account_codes[i] if payload.account_codes and i < len(payload.account_codes) else row.account_code),
            cost_center=(payload.cost_centers[i] if payload.cost_centers and i < len(payload.cost_centers) else row.cost_center),
            description=(payload.descriptions[i] if payload.descriptions and i < len(payload.descriptions) else row.description),
            amount=amount,
            currency=row.currency,
            created_by=current_user_id,
        )
        db.add(new_row)
        new_rows.append(new_row)

    await db.delete(row)
    await db.flush()
    await db.commit()
    for r in new_rows:
        await db.refresh(r)
    return new_rows


@router.post("/{company_id}/{invoice_id}/transaction-rows/merge", response_model=TransactionRowResponse)
async def merge_transaction_rows(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    payload: TransactionRowMergeRequest,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = []
    for row_id in payload.row_ids:
        row = await _get_transaction_row(invoice_id, row_id, db)
        rows.append(row)

    currencies = {r.currency for r in rows}
    if len(currencies) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot merge rows with different currencies",
        )

    total = sum(r.amount for r in rows)
    merged = TransactionRow(
        invoice_id=invoice_id,
        account_code=payload.account_code or rows[0].account_code,
        cost_center=payload.cost_center or rows[0].cost_center,
        description=payload.description or rows[0].description,
        amount=total,
        currency=rows[0].currency,
        created_by=current_user_id,
    )
    db.add(merged)
    for row in rows:
        await db.delete(row)
    await db.flush()
    await db.commit()
    await db.refresh(merged)
    return merged


# ──────────────────────────────────────────────
# Confirmation Flow
# ──────────────────────────────────────────────
@router.get("/{company_id}/{invoice_id}/confirmation-steps", response_model=list[ConfirmationStepResponse])
async def list_confirmation_steps(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_invoice(company_id, invoice_id, db)
    result = await db.execute(
        select(ConfirmationStep)
        .where(ConfirmationStep.invoice_id == invoice_id)
        .order_by(ConfirmationStep.step_order)
    )
    return result.scalars().all()


@router.post("/{company_id}/{invoice_id}/confirmation-steps", response_model=ConfirmationStepResponse, status_code=status.HTTP_201_CREATED)
async def add_confirmation_step(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    payload: ConfirmationStepCreate,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_invoice(company_id, invoice_id, db)
    step = ConfirmationStep(
        invoice_id=invoice_id,
        step_order=payload.step_order,
        assigned_to=payload.assigned_to,
    )
    db.add(step)
    await db.commit()
    await db.refresh(step)
    return step


@router.post("/{company_id}/{invoice_id}/confirmation-steps/{step_id}/decide", response_model=ConfirmationStepResponse)
async def decide_confirmation_step(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    step_id: uuid.UUID,
    payload: ConfirmationDecision,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invoice = await _get_invoice(company_id, invoice_id, db)
    result = await db.execute(
        select(ConfirmationStep).where(
            ConfirmationStep.id == step_id,
            ConfirmationStep.invoice_id == invoice_id,
            ConfirmationStep.assigned_to == current_user_id,
        )
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Step not found or not assigned to you")

    step.completed = True
    step.approved = payload.approved
    step.comment = payload.comment
    step.completed_at = datetime.now(timezone.utc)

    # Check if all steps are completed
    all_steps_result = await db.execute(
        select(ConfirmationStep).where(ConfirmationStep.invoice_id == invoice_id)
    )
    all_steps = all_steps_result.scalars().all()
    all_done = all(s.completed for s in all_steps)
    any_rejected = any(s.approved == False and s.completed for s in all_steps)  # noqa: E712

    if any_rejected:
        invoice.status = InvoiceStatus.REJECTED
    elif all_done:
        invoice.status = InvoiceStatus.APPROVED

    await db.commit()
    await db.refresh(step)
    return step


# ──────────────────────────────────────────────
# Comments
# ──────────────────────────────────────────────
@router.get("/{company_id}/{invoice_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_invoice(company_id, invoice_id, db)
    result = await db.execute(
        select(InvoiceComment).where(InvoiceComment.invoice_id == invoice_id)
    )
    return result.scalars().all()


@router.post("/{company_id}/{invoice_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    company_id: uuid.UUID,
    invoice_id: uuid.UUID,
    payload: CommentCreate,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_invoice(company_id, invoice_id, db)
    comment = InvoiceComment(
        invoice_id=invoice_id,
        user_id=current_user_id,
        content=payload.content,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


# ──────────────────────────────────────────────
# Automation Rules
# ──────────────────────────────────────────────
@router.get("/{company_id}/automation-rules", response_model=list[AutomationRuleResponse])
async def list_automation_rules(
    company_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InvoiceAutomationRule).where(InvoiceAutomationRule.company_id == company_id)
    )
    return result.scalars().all()


@router.post("/{company_id}/automation-rules", response_model=AutomationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_automation_rule(
    company_id: uuid.UUID,
    payload: AutomationRuleCreate,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rule = InvoiceAutomationRule(
        company_id=company_id,
        created_by=current_user_id,
        confirmation_user_ids=[str(uid) for uid in payload.confirmation_user_ids] if payload.confirmation_user_ids else None,
        **{k: v for k, v in payload.model_dump(exclude={"confirmation_user_ids"}).items()},
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{company_id}/automation-rules/{rule_id}")
async def delete_automation_rule(
    company_id: uuid.UUID,
    rule_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InvoiceAutomationRule).where(
            InvoiceAutomationRule.id == rule_id,
            InvoiceAutomationRule.company_id == company_id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"message": "Rule deleted"}


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────
async def _get_invoice(company_id: uuid.UUID, invoice_id: uuid.UUID, db: AsyncSession) -> Invoice:
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.company_id == company_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


async def _get_transaction_row(invoice_id: uuid.UUID, row_id: uuid.UUID, db: AsyncSession) -> TransactionRow:
    result = await db.execute(
        select(TransactionRow).where(
            TransactionRow.id == row_id,
            TransactionRow.invoice_id == invoice_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction row not found")
    return row
