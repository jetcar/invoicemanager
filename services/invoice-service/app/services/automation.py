"""
Automation engine: apply rules to create transaction rows for incoming invoices.
Rules are matched by supplier name pattern and description pattern (simple substring match).
Matched rules generate TransactionRow records automatically.
"""
from __future__ import annotations

import re
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice, InvoiceLine, TransactionRow, InvoiceAutomationRule, ConfirmationStep


async def apply_automation_rules(
    invoice: Invoice,
    created_by: uuid.UUID,
    db: AsyncSession,
) -> list[TransactionRow]:
    """
    Try to match automation rules for this invoice and create TransactionRows.
    Returns the list of created rows.
    """
    result = await db.execute(
        select(InvoiceAutomationRule)
        .where(
            InvoiceAutomationRule.company_id == invoice.company_id,
            InvoiceAutomationRule.is_active == True,  # noqa: E712
        )
        .order_by(InvoiceAutomationRule.priority.desc())
    )
    rules = result.scalars().all()

    created_rows: list[TransactionRow] = []
    assigned_users: set[uuid.UUID] = set()

    for line in invoice.lines:
        best_rule = _match_rule(rules, invoice, line)
        if best_rule:
            row = TransactionRow(
                invoice_id=invoice.id,
                invoice_line_id=line.id,
                account_code=best_rule.account_code,
                cost_center=best_rule.cost_center,
                description=line.description,
                amount=line.net_amount or line.total_amount or 0,
                currency=invoice.currency,
                created_by=created_by,
            )
            db.add(row)
            created_rows.append(row)

            if best_rule.confirmation_user_ids:
                for uid in best_rule.confirmation_user_ids:
                    assigned_users.add(uuid.UUID(str(uid)))

    if assigned_users and invoice.invoice_type.value == "purchase":
        # Create confirmation steps
        for step_order, user_id in enumerate(assigned_users, start=1):
            step = ConfirmationStep(
                invoice_id=invoice.id,
                step_order=step_order,
                assigned_to=user_id,
            )
            db.add(step)

    await db.flush()
    return created_rows


def _match_rule(
    rules: list[InvoiceAutomationRule],
    invoice: Invoice,
    line: InvoiceLine,
) -> Optional[InvoiceAutomationRule]:
    for rule in rules:
        if rule.supplier_name_pattern and invoice.supplier_name:
            if not re.search(rule.supplier_name_pattern, invoice.supplier_name, re.IGNORECASE):
                continue
        if rule.description_pattern and line.description:
            if not re.search(rule.description_pattern, line.description, re.IGNORECASE):
                continue
        return rule
    return None
