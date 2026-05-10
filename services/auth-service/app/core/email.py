import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from app.config import settings

_template_dir = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_template_dir)),
    autoescape=select_autoescape(["html", "xml"]),
)


async def send_email(to: str, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        start_tls=False,
    )


async def send_invite_email(to: str, token: str, inviter_name: str) -> None:
    url = f"{settings.app_base_url}/accept-invite?token={token}"
    html = f"""
    <h2>You have been invited to InvoiceManager</h2>
    <p>{inviter_name} has invited you to collaborate on InvoiceManager.</p>
    <p><a href="{url}">Accept Invitation</a></p>
    <p>This link expires in 7 days.</p>
    """
    await send_email(to, "InvoiceManager – Invitation", html)


async def send_verification_email(to: str, token: str) -> None:
    url = f"{settings.app_base_url}/verify-email?token={token}"
    html = f"""
    <h2>Verify your email address</h2>
    <p>Click the link below to verify your email address for InvoiceManager:</p>
    <p><a href="{url}">Verify Email</a></p>
    <p>This link expires in 24 hours.</p>
    """
    await send_email(to, "InvoiceManager – Email Verification", html)


async def send_password_reset_email(to: str, token: str) -> None:
    url = f"{settings.app_base_url}/reset-password?token={token}"
    html = f"""
    <h2>Password Reset Request</h2>
    <p>Click the link below to reset your InvoiceManager password:</p>
    <p><a href="{url}">Reset Password</a></p>
    <p>This link expires in 1 hour.</p>
    """
    await send_email(to, "InvoiceManager – Password Reset", html)


async def send_magic_link_email(to: str, token: str) -> None:
    url = f"{settings.app_base_url}/magic-login?token={token}"
    html = f"""
    <h2>Passwordless Login</h2>
    <p>Click the link below to log in to InvoiceManager (or scan the QR code in the app):</p>
    <p><a href="{url}">Log In</a></p>
    <p>This link expires in 15 minutes.</p>
    """
    await send_email(to, "InvoiceManager – Magic Login Link", html)
