import uuid
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.archive import ArchivedInvoice
from app.schemas.archive import ArchiveRequest, ArchivedInvoiceResponse

router = APIRouter(prefix="/api/v1/archive", tags=["archive"])


@router.post("/", response_model=ArchivedInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def archive_invoice(
    payload: ArchiveRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Called by the invoice-service (or a scheduled job) to move an invoice
    to cold storage. The caller must already have fetched the full invoice data.
    This endpoint stores it in the archive database.
    """
    existing = await db.execute(
        select(ArchivedInvoice).where(ArchivedInvoice.original_id == payload.invoice_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invoice already archived")

    # In production this would receive full invoice data from invoice-service
    from datetime import datetime, timezone
    archived = ArchivedInvoice(
        original_id=payload.invoice_id,
        company_id=payload.company_id,
        invoice_type="unknown",
        invoice_data={"original_id": str(payload.invoice_id)},
        original_created_at=datetime.now(timezone.utc),
    )
    db.add(archived)
    await db.commit()
    await db.refresh(archived)
    return archived


@router.get("/{company_id}", response_model=list[ArchivedInvoiceResponse])
async def list_archived(
    company_id: uuid.UUID,
    since: Optional[date] = Query(None),
    until: Optional[date] = Query(None),
    limit: int = Query(100, le=1000),
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ArchivedInvoice)
        .where(ArchivedInvoice.company_id == company_id)
        .order_by(ArchivedInvoice.archived_at.desc())
        .limit(limit)
    )
    if since:
        from datetime import datetime, timezone
        query = query.where(
            ArchivedInvoice.archived_at >= datetime(since.year, since.month, since.day, tzinfo=timezone.utc)
        )
    if until:
        from datetime import datetime, timezone
        query = query.where(
            ArchivedInvoice.archived_at <= datetime(until.year, until.month, until.day, 23, 59, 59, tzinfo=timezone.utc)
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{company_id}/{archive_id}", response_model=ArchivedInvoiceResponse)
async def get_archived(
    company_id: uuid.UUID,
    archive_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ArchivedInvoice).where(
            ArchivedInvoice.id == archive_id,
            ArchivedInvoice.company_id == company_id,
        )
    )
    archived = result.scalar_one_or_none()
    if not archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archived invoice not found")
    return archived
