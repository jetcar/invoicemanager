import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationRequest(BaseModel):
    user_id: uuid.UUID
    notification_type: str  # email | push | in_app
    subject: Optional[str] = None
    body: str
    extra_data: Optional[dict] = None
    # For email notifications
    email_address: Optional[str] = None
    # For push notifications
    push_token: Optional[str] = None


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str
    status: str
    subject: Optional[str]
    body: str
    created_at: datetime
    sent_at: Optional[datetime]

    model_config = {"from_attributes": True}
