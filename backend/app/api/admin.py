"""Admin API — user management (admin only)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class UserAdminResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    tier: str = "free"
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    role: str  # admin / user
    tier: Optional[str] = None  # free / pro / enterprise
    is_active: Optional[bool] = None


@router.get("/users", response_model=List[UserAdminResponse])
async def list_users(
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at))
    return result.scalars().all()


@router.put("/users/{user_id}", response_model=UserAdminResponse)
async def update_user(
    user_id: int,
    data: UserRoleUpdate,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if data.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="角色只能是 admin 或 user")
    if data.tier is not None and data.tier not in ("free", "pro", "enterprise"):
        raise HTTPException(status_code=400, detail="套餐只能是 free、pro 或 enterprise")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.role = data.role
    user.is_admin = data.role == "admin"
    if data.tier is not None:
        user.tier = data.tier
    if data.is_active is not None:
        user.is_active = data.is_active

    await db.flush()
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.delete(user)
    return {"message": "用户已删除"}
