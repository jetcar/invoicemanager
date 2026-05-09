import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.notification import Notification, NotificationType, NotificationStatus
from app.schemas.notification import NotificationRequest, NotificationResponse
from app.services.sender import send_notification

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.post("/send", response_model=NotificationResponse)
async def send(
    payload: NotificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Internal endpoint – called by other services to dispatch notifications."""
    notif = Notification(
        user_id=payload.user_id,
        notification_type=NotificationType(payload.notification_type),
        subject=payload.subject,
        body=payload.body,
        extra_data=payload.extra_data,
    )
    db.add(notif)
    await db.flush()

    try:
        await send_notification(notif, payload)
        notif.status = NotificationStatus.SENT
        notif.sent_at = datetime.now(timezone.utc)
    except Exception as exc:
        notif.status = NotificationStatus.FAILED
        notif.error_message = str(exc)

    await db.commit()
    await db.refresh(notif)
    return notif


@router.get("/user/{user_id}", response_model=list[NotificationResponse])
async def user_notifications(
    user_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(100)
    )
    return result.scalars().all()
