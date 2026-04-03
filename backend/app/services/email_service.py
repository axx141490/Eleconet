"""Email service — SMTP sending via SSL."""

import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import get_settings

_UPPERCASE = string.ascii_uppercase
_LOWERCASE = string.ascii_lowercase
_DIGITS = string.digits
_SYMBOLS = "!@#$%^&*()-_=+"
_ALL = _UPPERCASE + _LOWERCASE + _DIGITS + _SYMBOLS


def generate_password(length: int = 12) -> str:
    """Generate a random password satisfying all strength rules."""
    # Guarantee at least one character from each required category
    chars = [
        random.choice(_UPPERCASE),
        random.choice(_LOWERCASE),
        random.choice(_DIGITS),
        random.choice(_SYMBOLS),
    ]
    # Fill the rest randomly from the full pool
    chars += random.choices(_ALL, k=length - 4)
    random.shuffle(chars)
    return "".join(chars)


def send_password_reset_email(to_email: str, username: str, new_password: str) -> None:
    """Send a password-reset notification email via SMTP SSL."""
    settings = get_settings()
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        raise RuntimeError("SMTP 未配置，请在 .env 中设置 SMTP_HOST / SMTP_USER / SMTP_PASSWORD / SMTP_FROM")

    subject = "【RAG 智能知识库】您的密码已被重置"
    body = f"""您好，{username}：

系统管理员已重置您的登录密码，新密码如下：

    {new_password}

请使用新密码登录后立即前往「个人设置」修改密码。

如有疑问，请联系管理员。

RAG 智能知识库团队
"""

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(msg["From"], to_email, msg.as_string())
