"""
Notification sender: dispatches email and push notifications.
Firebase Cloud Messaging is used for push notifications.
"""
from __future__ import annotations

import json
from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationRequest
from app.config import settings


async def send_notification(notif: Notification, payload: NotificationRequest) -> None:
    if notif.notification_type == NotificationType.EMAIL:
        await _send_email(payload)
    elif notif.notification_type == NotificationType.PUSH:
        await _send_push(payload)
    # in_app notifications are stored in the DB and read by the client


async def _send_email(payload: NotificationRequest) -> None:
    import aiosmtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    if not payload.email_address:
        raise ValueError("email_address is required for email notifications")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = payload.subject or "InvoiceManager Notification"
    msg["From"] = settings.smtp_from
    msg["To"] = payload.email_address
    msg.attach(MIMEText(payload.body, "html"))

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=int(settings.smtp_port),
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        start_tls=False,
    )


async def _send_push(payload: NotificationRequest) -> None:
    """
    Send push notification via Firebase Cloud Messaging HTTP v1 API.
    Requires FIREBASE_CREDENTIALS_JSON environment variable to be set.
    """
    import httpx
    from app.config import settings

    firebase_creds = settings.firebase_credentials_json
    if not firebase_creds:
        raise ValueError("FIREBASE_CREDENTIALS_JSON not configured")

    push_token = payload.push_token or (payload.extra_data or {}).get("push_token")
    if not push_token:
        raise ValueError("push_token is required for push notifications")

    # Build FCM HTTP v1 request (simplified – production code would use google-auth)
    creds = json.loads(firebase_creds)
    project_id = creds.get("project_id")
    fcm_url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

    fcm_payload = {
        "message": {
            "token": push_token,
            "notification": {
                "title": payload.subject or "InvoiceManager",
                "body": payload.body,
            },
            "data": {k: str(v) for k, v in (payload.extra_data or {}).items()},
        }
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(fcm_url, json=fcm_payload, timeout=10)
        resp.raise_for_status()
