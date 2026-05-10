import uuid
import pyotp
import qrcode
import io
import base64
from typing import Optional


def generate_totp_secret() -> str:
    """Generate a new TOTP secret for 2FA."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, user_email: str, issuer: str = "InvoiceManager") -> str:
    """Return the otpauth URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=user_email, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code. Allows 1 step drift."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def generate_qr_code_base64(uri: str) -> str:
    """Return a base64-encoded PNG QR code image."""
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode()


def generate_login_session_token() -> str:
    """Generate a random token for QR-code-based passwordless login."""
    return str(uuid.uuid4())
