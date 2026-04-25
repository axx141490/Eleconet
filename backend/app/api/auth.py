"""Authentication API endpoints."""

import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.user import User
from app.api.schemas import UserRegister, UserLogin, UserResponse, TokenResponse
from app.services.sms_service import load_sms_config, send_sms_code, verify_code
from app.api.settings import load_session_config

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ChangeEmailRequest(BaseModel):
    new_email: str
    current_password: str


class ChangePhoneRequest(BaseModel):
    new_phone: str
    current_password: str


class SendSmsRequest(BaseModel):
    phone: str
    scene: str = "register"   # register | login


class SmsLoginRequest(BaseModel):
    phone: str
    sms_code: str


@router.post("/send-sms-code")
async def send_sms(data: SendSmsRequest, db: AsyncSession = Depends(get_db)):
    """Send SMS verification code. scene=login requires phone to be registered."""
    if data.scene == "login":
        result = await db.execute(select(User).where(User.phone == data.phone))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="该手机号未注册")
    try:
        send_sms_code(data.phone)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "验证码已发送"}


@router.post("/login-sms", response_model=TokenResponse)
async def login_sms(data: SmsLoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with phone number + SMS verification code."""
    sms_cfg = load_sms_config()
    if not sms_cfg.get("enabled"):
        raise HTTPException(status_code=400, detail="短信验证未启用")

    if not verify_code(data.phone, data.sms_code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    result = await db.execute(select(User).where(User.phone == data.phone))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="该手机号未注册")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    expire_hours = load_session_config().get("token_expire_hours", 24)
    token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(hours=expire_hours))
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    sms_cfg = load_sms_config()

    # Phone verification when required
    if sms_cfg.get("enabled") and sms_cfg.get("require_phone_on_register"):
        if not data.phone:
            raise HTTPException(status_code=400, detail="请填写手机号")
        if not data.sms_code:
            raise HTTPException(status_code=400, detail="请填写短信验证码")
        if not verify_code(data.phone, data.sms_code):
            raise HTTPException(status_code=400, detail="验证码错误或已过期")

    existing = await db.execute(
        select(User).where((User.username == data.username) | (User.email == data.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名或邮箱已被注册")

    if data.phone:
        phone_exists = await db.execute(select(User).where(User.phone == data.phone))
        if phone_exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="该手机号已被注册")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        phone=data.phone or None,
    )
    db.add(user)
    await db.flush()

    expire_hours = load_session_config().get("token_expire_hours", 24)
    token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(hours=expire_hours))
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with username or phone number."""
    result = await db.execute(
        select(User).where(
            (User.username == data.username) | (User.phone == data.username) | (func.lower(User.email) == data.username.lower())
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    expire_hours = load_session_config().get("token_expire_hours", 24)
    token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(hours=expire_hours))
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.put("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    try:
        from app.api.schemas import validate_password_strength
        validate_password_strength(data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    current_user.hashed_password = hash_password(data.new_password)
    current_user.updated_at = datetime.utcnow()
    await db.flush()
    return {"message": "密码已修改"}


@router.put("/change-email", response_model=UserResponse)
async def change_email(
    data: ChangeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's email."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="密码不正确")

    existing = await db.execute(
        select(User).where(User.email == data.new_email, User.id != current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该邮箱已被其他账号使用")

    current_user.email = data.new_email
    current_user.updated_at = datetime.utcnow()
    await db.flush()
    return UserResponse.model_validate(current_user)


@router.put("/change-phone", response_model=UserResponse)
async def change_phone(
    data: ChangePhoneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's phone number."""
    if not re.match(r'^\d{11}$', data.new_phone):
        raise HTTPException(status_code=400, detail="手机号必须为 11 位数字")
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="密码不正确")

    existing = await db.execute(
        select(User).where(User.phone == data.new_phone, User.id != current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该手机号已被其他账号使用")

    current_user.phone = data.new_phone
    current_user.updated_at = datetime.utcnow()
    await db.flush()
    return UserResponse.model_validate(current_user)
