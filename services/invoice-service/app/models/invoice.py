import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import (
    String, Boolean, DateTime, Text, ForeignKey, Enum, Numeric,
    Date, Integer, JSON, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class InvoiceType(str, PyEnum):
    PURCHASE = "purchase"
    SALES = "sales"


class InvoiceStatus(str, PyEnum):
    DRAFT = "draft"
    PENDING = "pending"          # awaiting confirmation
    IN_REVIEW = "in_review"      # assigned to processor
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPORTED = "exported"
    ARCHIVED = "archived"


class InvoiceSource(str, PyEnum):
    MANUAL = "manual"
    API = "api"
    EINVOICE_ET = "einvoice_et"   # Estonian e-invoice 1.2
    UBL = "ubl"


class TransactionRowStatus(str, PyEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    invoice_type: Mapped[InvoiceType] = mapped_column(Enum(InvoiceType), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT
    )
    source: Mapped[InvoiceSource] = mapped_column(
        Enum(InvoiceSource), nullable=False, default=InvoiceSource.MANUAL
    )
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=True)
    supplier_reg_code: Mapped[str] = mapped_column(String(100), nullable=True)
    supplier_vat_code: Mapped[str] = mapped_column(String(100), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=True)
    customer_reg_code: Mapped[str] = mapped_column(String(100), nullable=True)
    customer_vat_code: Mapped[str] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=True)
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    raw_xml: Mapped[str] = mapped_column(Text, nullable=True)   # original e-invoice XML
    extra_data: Mapped[dict] = mapped_column(JSONB, nullable=True)
    assigned_to: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    lines: Mapped[list["InvoiceLine"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    transaction_rows: Mapped[list["TransactionRow"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    confirmation_steps: Mapped[list["ConfirmationStep"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    comments: Mapped[list["InvoiceComment"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=True)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=True)
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=True)
    account_code: Mapped[str] = mapped_column(String(50), nullable=True)
    cost_center: Mapped[str] = mapped_column(String(100), nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSONB, nullable=True)

    invoice: Mapped["Invoice"] = relationship(back_populates="lines")
    transaction_rows: Mapped[list["TransactionRow"]] = relationship(
        back_populates="invoice_line", cascade="all, delete-orphan"
    )


class TransactionRow(Base):
    """Accounting transaction rows derived from invoice lines."""

    __tablename__ = "transaction_rows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoice_lines.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[TransactionRowStatus] = mapped_column(
        Enum(TransactionRowStatus), nullable=False, default=TransactionRowStatus.DRAFT
    )
    account_code: Mapped[str] = mapped_column(String(50), nullable=True)
    cost_center: Mapped[str] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="transaction_rows")
    invoice_line: Mapped["InvoiceLine"] = relationship(back_populates="transaction_rows")


class ConfirmationStep(Base):
    """Represents a single confirmation step in the invoice approval workflow."""

    __tablename__ = "confirmation_steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    assigned_to: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="confirmation_steps")


class InvoiceComment(Base):
    __tablename__ = "invoice_comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="comments")


class InvoiceAutomationRule(Base):
    """AI/rule-based automation rules for creating transaction rows."""

    __tablename__ = "invoice_automation_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name_pattern: Mapped[str] = mapped_column(String(255), nullable=True)
    description_pattern: Mapped[str] = mapped_column(String(255), nullable=True)
    account_code: Mapped[str] = mapped_column(String(50), nullable=True)
    cost_center: Mapped[str] = mapped_column(String(100), nullable=True)
    confirmation_user_ids: Mapped[list] = mapped_column(JSONB, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
