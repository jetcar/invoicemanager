import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ArchivedInvoice(Base):
    """Cold storage copy of an invoice moved out of the active invoice database."""

    __tablename__ = "archived_invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True, unique=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    invoice_type: Mapped[str] = mapped_column(String(20), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=True)
    invoice_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    raw_xml: Mapped[str] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    original_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
