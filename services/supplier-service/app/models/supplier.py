import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Supplier(Base):
    """
    A supplier can belong to a specific company (company_id set) or be in the
    shared global list (company_id is NULL). Company-specific suppliers are
    private; shared suppliers are visible to all verified companies.
    """

    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("company_id", "reg_code", name="uq_supplier_company_reg"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    reg_code: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    vat_code: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    iban: Mapped[str] = mapped_column(String(100), nullable=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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
