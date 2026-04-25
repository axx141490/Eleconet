"""Email service — SMTP sending via SSL."""

import smtplib
import random
import string
import time
from typing import Dict, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import get_settings

# ── Email verification code store ──────────────────────────────────────────
_email_code_store: Dict[str, Tuple[str, float]] = {}
_email_last_sent: Dict[str, float] = {}
_email_verify_failures: Dict[str, Tuple[int, float]] = {}

EMAIL_CODE_TTL = 300       # 5 分钟有效
EMAIL_CODE_COOLDOWN = 60   # 60 秒内不可重复发送
MAX_VERIFY_ATTEMPTS = 5
VERIFY_LOCKOUT = 600       # 锁定 10 分钟


def send_email_code(to_email: str) -> None:
    """Generate and send a 6-digit verification code to the given email."""
    now = time.time()
    last = _email_last_sent.get(to_email, 0)
    if now - last < EMAIL_CODE_COOLDOWN:
        remaining = int(EMAIL_CODE_COOLDOWN - (now - last))
        raise RuntimeError(f"发送过于频繁，请 {remaining} 秒后再试")

    code = str(random.randint(100000, 999999))
    _email_code_store[to_email] = (code, now + EMAIL_CODE_TTL)
    _email_last_sent[to_email] = now

    settings = get_settings()
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        raise RuntimeError("SMTP 未配置，无法发送验证码")

    subject = "【RAG 智能知识库】邮箱验证码"
    body = f"您的验证码为：{code}\n\n验证码 5 分钟内有效，请勿泄露给他人。"

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(msg["From"], to_email, msg.as_string())


def verify_email_code(email: str, code: str) -> bool:
    """Verify the email code; raises RuntimeError if locked out."""
    now = time.time()
    failures, locked_until = _email_verify_failures.get(email, (0, 0))
    if locked_until > now:
        remaining = int(locked_until - now)
        raise RuntimeError(f"验证码错误次数过多，请 {remaining} 秒后再试")

    entry = _email_code_store.get(email)
    if not entry:
        return False
    stored_code, expire_at = entry
    if now > expire_at:
        _email_code_store.pop(email, None)
        return False
    if stored_code != code:
        failures += 1
        if failures >= MAX_VERIFY_ATTEMPTS:
            _email_verify_failures[email] = (failures, now + VERIFY_LOCKOUT)
        else:
            _email_verify_failures[email] = (failures, 0)
        return False

    _email_code_store.pop(email, None)
    _email_verify_failures.pop(email, None)
    return True

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
