import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.totp import (
    generate_totp_secret,
    get_totp_uri,
    verify_totp,
    generate_qr_code_base64,
    generate_login_session_token,
)
from app.core.email import (
    send_verification_email,
    send_password_reset_email,
    send_invite_email,
    send_magic_link_email,
)
from app.models.user import (
    User,
    RefreshToken,
    Invitation,
    EmailVerificationToken,
    PasswordResetToken,
    MagicLoginSession,
)
from app.schemas.auth import (
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TOTPSetupResponse,
    TOTPEnableRequest,
    InvitationCreateRequest,
    InvitationAcceptRequest,
    InvitationResponse,
    MagicLinkRequest,
    MagicLoginPollResponse,
    QRLoginSessionResponse,
    PushTokenRegisterRequest,
)
from app.services.auth_deps import (
    get_current_user,
    get_current_superadmin,
    hash_token,
    generate_secure_token,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ──────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
    )
    db.add(user)
    await db.flush()

    token_str = generate_secure_token()
    ev_token = EmailVerificationToken(
        user_id=user.id,
        token=token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(ev_token)
    await db.commit()
    await db.refresh(user)

    background_tasks.add_task(send_verification_email, payload.email, token_str)
    return user


@router.post("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token == token,
            EmailVerificationToken.used == False,  # noqa: E712
            EmailVerificationToken.expires_at > datetime.now(timezone.utc),
        )
    )
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user_result = await db.execute(select(User).where(User.id == ev.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_verified = True
    ev.used = True
    await db.commit()
    return {"message": "Email verified successfully"}


# ──────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    if user.totp_enabled:
        if not payload.totp_code:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="2FA code required",
            )
        if not verify_totp(user.totp_secret, payload.totp_code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token_str = generate_secure_token(48)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token_str),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(rt)
    await db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(payload.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    rt = result.scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # Rotate: revoke old, issue new
    rt.revoked = True
    new_refresh_str = generate_secure_token(48)
    new_rt = RefreshToken(
        user_id=rt.user_id,
        token_hash=hash_token(new_refresh_str),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(new_rt)
    await db.commit()

    access_token = create_access_token({"sub": str(rt.user_id)})
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_str)


@router.post("/logout")
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(payload.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    rt = result.scalar_one_or_none()
    if rt:
        rt.revoked = True
        await db.commit()
    return {"message": "Logged out"}


# ──────────────────────────────────────────────
# Current user
# ──────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.first_name is not None:
        current_user.first_name = payload.first_name
    if payload.last_name is not None:
        current_user.last_name = payload.last_name
    if payload.phone is not None:
        current_user.phone = payload.phone
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    current_user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()
    return {"message": "Password changed"}


# ──────────────────────────────────────────────
# Password reset
# ──────────────────────────────────────────────
@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user:
        token_str = generate_secure_token()
        pr = PasswordResetToken(
            user_id=user.id,
            token=token_str,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(pr)
        await db.commit()
        background_tasks.add_task(send_password_reset_email, payload.email, token_str)
    # Always return 200 to prevent enumeration
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == payload.token,
            PasswordResetToken.used == False,  # noqa: E712
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
    )
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user_result = await db.execute(select(User).where(User.id == pr.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = get_password_hash(payload.new_password)
    pr.used = True
    await db.commit()
    return {"message": "Password reset successful"}


# ──────────────────────────────────────────────
# TOTP / 2FA
# ──────────────────────────────────────────────
@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def totp_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    secret = generate_totp_secret()
    current_user.totp_secret = secret
    await db.commit()
    uri = get_totp_uri(secret, current_user.email)
    qr = generate_qr_code_base64(uri)
    return TOTPSetupResponse(secret=secret, qr_code_base64=qr, otpauth_uri=uri)


@router.post("/totp/enable")
async def totp_enable(
    payload: TOTPEnableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Setup TOTP first")
    if not verify_totp(current_user.totp_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")
    current_user.totp_enabled = True
    await db.commit()
    return {"message": "2FA enabled"}


@router.post("/totp/disable")
async def totp_disable(
    payload: TOTPEnableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is not enabled")
    if not verify_totp(current_user.totp_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")
    current_user.totp_enabled = False
    current_user.totp_secret = None
    await db.commit()
    return {"message": "2FA disabled"}


# ──────────────────────────────────────────────
# Invitations
# ──────────────────────────────────────────────
@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    payload: InvitationCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token_str = generate_secure_token()
    invite = Invitation(
        email=payload.email,
        token=token_str,
        company_id=payload.company_id,
        role=payload.role,
        created_by=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    inviter_name = f"{current_user.first_name} {current_user.last_name}"
    background_tasks.add_task(send_invite_email, payload.email, token_str, inviter_name)
    return invite


@router.post("/invitations/accept", response_model=TokenResponse)
async def accept_invitation(
    payload: InvitationAcceptRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Invitation).where(
            Invitation.token == payload.token,
            Invitation.accepted == False,  # noqa: E712
            Invitation.expires_at > datetime.now(timezone.utc),
        )
    )
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invitation")

    # Check if user already exists
    user_result = await db.execute(select(User).where(User.email == invite.email))
    user = user_result.scalar_one_or_none()

    if user:
        # User exists – just mark invitation accepted
        invite.accepted = True
        await db.commit()
    else:
        # Create new user
        user = User(
            email=invite.email,
            hashed_password=get_password_hash(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            is_verified=True,  # trusted via invite
        )
        db.add(user)
        await db.flush()
        invite.accepted = True
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_str = generate_secure_token(48)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_str),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(rt)
    await db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_str)


# ──────────────────────────────────────────────
# Passwordless / Magic Link / QR Login
# ──────────────────────────────────────────────
@router.post("/magic-link")
async def request_magic_link(
    payload: MagicLinkRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user:
        token_str = generate_login_session_token()
        session = MagicLoginSession(
            token=token_str,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )
        db.add(session)
        await db.commit()
        background_tasks.add_task(send_magic_link_email, payload.email, token_str)
    return {"message": "If the email exists, a login link has been sent"}


@router.get("/magic-link/poll/{session_token}", response_model=MagicLoginPollResponse)
async def poll_magic_link(session_token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MagicLoginSession).where(MagicLoginSession.token == session_token)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if session.expires_at < datetime.now(timezone.utc):
        return MagicLoginPollResponse(status="expired")

    if not session.confirmed:
        return MagicLoginPollResponse(status="pending")

    # Issue tokens
    access_token = create_access_token({"sub": str(session.user_id)})
    refresh_str = generate_secure_token(48)
    rt = RefreshToken(
        user_id=session.user_id,
        token_hash=hash_token(refresh_str),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(rt)
    await db.delete(session)
    await db.commit()
    return MagicLoginPollResponse(status="confirmed", access_token=access_token, refresh_token=refresh_str)


@router.post("/magic-link/confirm/{session_token}")
async def confirm_magic_link(
    session_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Called by the mobile app after scanning QR code to confirm login."""
    result = await db.execute(
        select(MagicLoginSession).where(
            MagicLoginSession.token == session_token,
            MagicLoginSession.expires_at > datetime.now(timezone.utc),
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or expired")

    session.user_id = current_user.id
    session.confirmed = True
    await db.commit()
    return {"message": "Login confirmed"}


@router.get("/qr-login/session", response_model=QRLoginSessionResponse)
async def generate_qr_login_session(db: AsyncSession = Depends(get_db)):
    """Browser calls this to get a QR code for passwordless login."""
    token_str = generate_login_session_token()
    session = MagicLoginSession(
        token=token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add(session)
    await db.commit()

    from app.config import settings
    qr_uri = f"{settings.app_base_url}/qr-login?token={token_str}"
    qr_base64 = generate_qr_code_base64(qr_uri)
    return QRLoginSessionResponse(session_token=token_str, qr_code_base64=qr_base64)


# ──────────────────────────────────────────────
# Mobile push token
# ──────────────────────────────────────────────
@router.post("/push-token")
async def register_push_token(
    payload: PushTokenRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.mobile_push_token = payload.push_token
    await db.commit()
    return {"message": "Push token registered"}


# ──────────────────────────────────────────────
# Superadmin: list users
# ──────────────────────────────────────────────
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    return result.scalars().all()


@router.patch("/users/{user_id}/activate")
async def activate_user(
    user_id: uuid.UUID,
    _: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = True
    await db.commit()
    return {"message": "User activated"}


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: uuid.UUID,
    _: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = False
    await db.commit()
    return {"message": "User deactivated"}
