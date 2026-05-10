import uuid
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogCreate, AuditLogResponse

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.post("/log", response_model=AuditLogResponse, status_code=201)
async def log_action(
    payload: AuditLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """Internal endpoint – called by other services to log actions."""
    entry = AuditLog(**payload.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("/logs", response_model=list[AuditLogResponse])
async def list_logs(
    user_id: Optional[uuid.UUID] = Query(None),
    company_id: Optional[uuid.UUID] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    since: Optional[date] = Query(None),
    until: Optional[date] = Query(None),
    limit: int = Query(100, le=1000),
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if company_id:
        query = query.where(AuditLog.company_id == company_id)
    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)
    if since:
        from datetime import datetime, timezone
        query = query.where(AuditLog.created_at >= datetime(since.year, since.month, since.day, tzinfo=timezone.utc))
    if until:
        from datetime import datetime, timezone
        query = query.where(AuditLog.created_at <= datetime(until.year, until.month, until.day, 23, 59, 59, tzinfo=timezone.utc))
    result = await db.execute(query)
    return result.scalars().all()
