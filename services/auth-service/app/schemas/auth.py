import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ──────────────────────────────────────────────
# User schemas
# ──────────────────────────────────────────────
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    is_active: bool
    is_verified: bool
    is_superadmin: bool
    totp_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None


# ──────────────────────────────────────────────
# Auth schemas
# ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


# ──────────────────────────────────────────────
# TOTP / 2FA schemas
# ──────────────────────────────────────────────
class TOTPSetupResponse(BaseModel):
    secret: str
    qr_code_base64: str
    otpauth_uri: str


class TOTPEnableRequest(BaseModel):
    code: str


class TOTPVerifyRequest(BaseModel):
    code: str


# ──────────────────────────────────────────────
# Invitation schemas
# ──────────────────────────────────────────────
class InvitationCreateRequest(BaseModel):
    email: EmailStr
    company_id: Optional[uuid.UUID] = None
    role: Optional[str] = None


class InvitationAcceptRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = None


class InvitationResponse(BaseModel):
    id: uuid.UUID
    email: str
    company_id: Optional[uuid.UUID]
    role: Optional[str]
    accepted: bool
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Passwordless / Magic Link schemas
# ──────────────────────────────────────────────
class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLoginPollResponse(BaseModel):
    status: str  # "pending" | "confirmed" | "expired"
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class QRLoginSessionResponse(BaseModel):
    session_token: str
    qr_code_base64: str


class PushTokenRegisterRequest(BaseModel):
    push_token: str
