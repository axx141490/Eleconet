"""Authentication and security utilities."""

from datetime import datetime, timedelta
from typing import Optional
import bcrypt as _bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import get_settings
from app.core.database import get_db

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Get the current authenticated user (admin or user)."""
    from app.models.user import User

    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated",
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    # Auto-downgrade if paid tier has expired
    if user.tier != "free" and not user.is_admin and user.tier_expires_at is not None:
        if user.tier_expires_at < datetime.utcnow():
            user.tier = "free"
            await db.flush()

    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Optionally get the current user (returns None if not authenticated)."""
    if token is None:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


async def require_admin(current_user=Depends(get_current_user)):
    """Dependency: require admin role."""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


async def verify_share_token(
    share_token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Validate a guest share token. Returns (kb_id) if valid."""
    from app.models.user import ShareLink

    if not share_token:
        return None

    result = await db.execute(select(ShareLink).where(ShareLink.token == share_token))
    link = result.scalar_one_or_none()

    if link is None:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    if link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="分享链接已过期")

    return link
