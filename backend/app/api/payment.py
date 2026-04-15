"""Payment API — order creation, status polling, and payment callbacks."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.models.payment import PaymentOrder
from app.services import payment_service as ps

router = APIRouter(prefix="/api/payment", tags=["Payment"])


# ── Schemas ────────────────────────────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    tier: str           # pro / enterprise
    duration_months: int  # 1 or 12
    pay_method: str     # wechat / alipay


class OrderStatusResponse(BaseModel):
    order_no: str
    status: str
    pay_method: str
    tier: str
    duration_months: int
    amount_fen: int
    qr_code_url: Optional[str] = None
    paid_at: Optional[datetime] = None


class PaymentConfigUpdate(BaseModel):
    pricing: Optional[dict] = None
    wechat: Optional[dict] = None
    alipay: Optional[dict] = None


# ── Helpers ────────────────────────────────────────────────────────────────

def _tier_duration(tier: str, duration_months: int) -> datetime:
    """Compute new tier_expires_at from now."""
    if duration_months == 12:
        return datetime.utcnow() + timedelta(days=366)
    return datetime.utcnow() + timedelta(days=31)


async def _activate_tier(user_id: int, tier: str, duration_months: int,
                          order_no: str, trade_no: str, db: AsyncSession):
    """Mark order paid and upgrade user tier."""
    result = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == order_no))
    order = result.scalar_one_or_none()
    if not order or order.status == "paid":
        return

    order.status = "paid"
    order.trade_no = trade_no
    order.paid_at = datetime.utcnow()
    order.expires_at = _tier_duration(tier, duration_months)

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user:
        user.tier = tier
        # Extend existing subscription if not expired
        now = datetime.utcnow()
        base = user.tier_expires_at if user.tier_expires_at and user.tier_expires_at > now else now
        if duration_months == 12:
            user.tier_expires_at = base + timedelta(days=366)
        else:
            user.tier_expires_at = base + timedelta(days=31)

    await db.flush()


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/plans")
async def get_plans():
    """Public: return pricing plans and which payment methods are enabled."""
    config = ps.load_config()
    pricing = config["pricing"]
    return {
        "plans": [
            {
                "tier": "free",
                "name": "Free",
                "monthly_fen": 0,
                "yearly_fen": 0,
                "features": ["5个知识库", "每库10篇文档", "1MB文件限制", "基础文件格式", "10条对话历史"],
            },
            {
                "tier": "pro",
                "name": "Pro",
                "monthly_fen": pricing["pro_monthly"],
                "yearly_fen": pricing["pro_yearly"],
                "features": ["100个知识库", "每库100篇文档", "1GB文件限制", "全部文件格式", "分享链接", "100条对话历史"],
            },
            {
                "tier": "enterprise",
                "name": "Enterprise",
                "monthly_fen": pricing["enterprise_monthly"],
                "yearly_fen": pricing["enterprise_yearly"],
                "features": ["100个知识库", "每库1000篇文档", "1GB文件限制", "全部文件格式", "分享链接", "1000条对话历史"],
            },
        ],
        "wechat_enabled": config["wechat"].get("enabled", False),
        "alipay_enabled": config["alipay"].get("enabled", False),
        "alipay_sandbox": config["alipay"].get("sandbox", False),
    }


@router.post("/create-order", response_model=OrderStatusResponse)
async def create_order(
    data: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a payment order and return QR / payment URL."""
    if data.tier not in ("pro", "enterprise"):
        raise HTTPException(status_code=400, detail="套餐只能是 pro 或 enterprise")
    if data.duration_months not in (1, 12):
        raise HTTPException(status_code=400, detail="时长只能是 1 或 12 个月")
    if data.pay_method not in ("wechat", "alipay"):
        raise HTTPException(status_code=400, detail="支付方式只能是 wechat 或 alipay")

    config = ps.load_config()
    if data.pay_method == "wechat" and not config["wechat"].get("enabled"):
        raise HTTPException(status_code=400, detail="微信支付未配置")
    if data.pay_method == "alipay" and not config["alipay"].get("enabled"):
        raise HTTPException(status_code=400, detail="支付宝未配置")

    amount_fen = ps.get_price(data.tier, data.duration_months)
    if amount_fen <= 0:
        raise HTTPException(status_code=500, detail="价格配置错误")

    order_no = ps.make_order_no()
    qr_code_url = None

    if data.pay_method == "wechat":
        qr_code_url = await ps.wechat_create_native(order_no, amount_fen, data.tier, data.duration_months)
        if not qr_code_url:
            raise HTTPException(status_code=502, detail="微信支付下单失败，请检查配置")
    else:
        qr_code_url = await ps.alipay_create_order(order_no, amount_fen, data.tier, data.duration_months)
        if not qr_code_url:
            raise HTTPException(status_code=502, detail="支付宝下单失败，请检查配置")

    order = PaymentOrder(
        order_no=order_no,
        user_id=current_user.id,
        tier=data.tier,
        duration_months=data.duration_months,
        amount_fen=amount_fen,
        pay_method=data.pay_method,
        status="pending",
        qr_code_url=qr_code_url,
    )
    db.add(order)
    await db.flush()

    return OrderStatusResponse(
        order_no=order.order_no,
        status=order.status,
        pay_method=order.pay_method,
        tier=order.tier,
        duration_months=order.duration_months,
        amount_fen=order.amount_fen,
        qr_code_url=order.qr_code_url,
    )


@router.get("/order/{order_no}", response_model=OrderStatusResponse)
async def get_order_status(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Poll order status. Also queries the payment provider if still pending."""
    result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.order_no == order_no,
            PaymentOrder.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # If still pending, query provider
    if order.status == "pending":
        if order.pay_method == "wechat":
            status = await ps.wechat_query_order(order_no)
        else:
            status = await ps.alipay_query_order(order_no)

        if status == "paid":
            await _activate_tier(current_user.id, order.tier, order.duration_months,
                                  order_no, order_no, db)
            order.status = "paid"

    return OrderStatusResponse(
        order_no=order.order_no,
        status=order.status,
        pay_method=order.pay_method,
        tier=order.tier,
        duration_months=order.duration_months,
        amount_fen=order.amount_fen,
        qr_code_url=order.qr_code_url,
        paid_at=order.paid_at,
    )


@router.post("/callback/wechat")
async def wechat_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """WeChat Pay async notification callback."""
    body = await request.body()
    headers = dict(request.headers)

    resource = ps.wechat_verify_callback(headers, body)
    if not resource:
        return {"code": "FAIL", "message": "验签失败"}

    out_trade_no = resource.get("out_trade_no", "")
    trade_no = resource.get("transaction_id", "")
    trade_state = resource.get("trade_state", "")

    if trade_state == "SUCCESS" and out_trade_no:
        result = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == out_trade_no))
        order = result.scalar_one_or_none()
        if order:
            await _activate_tier(order.user_id, order.tier, order.duration_months,
                                  out_trade_no, trade_no, db)
            await db.commit()

    return {"code": "SUCCESS", "message": "成功"}


@router.post("/callback/alipay")
async def alipay_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Alipay async notification callback."""
    form = await request.form()
    data = dict(form)

    if not ps.alipay_verify_callback(data.copy()):
        return "fail"

    out_trade_no = data.get("out_trade_no", "")
    trade_no = data.get("trade_no", "")
    trade_status = data.get("trade_status", "")

    if trade_status == "TRADE_SUCCESS" and out_trade_no:
        result = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == out_trade_no))
        order = result.scalar_one_or_none()
        if order:
            await _activate_tier(order.user_id, order.tier, order.duration_months,
                                  out_trade_no, trade_no, db)
            await db.commit()

    return "success"


@router.post("/simulate-pay/{order_no}")
async def simulate_pay(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sandbox only: instantly mark an order as paid for testing."""
    config = ps.load_config()
    # Only allow when alipay sandbox mode is on or wechat not configured
    alipay_sandbox = config.get("alipay", {}).get("sandbox", False)
    wechat_enabled = config.get("wechat", {}).get("enabled", False)
    if not alipay_sandbox and wechat_enabled:
        raise HTTPException(status_code=403, detail="仅沙箱模式下可模拟支付")

    result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.order_no == order_no,
            PaymentOrder.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status == "paid":
        return {"message": "已支付"}

    await _activate_tier(current_user.id, order.tier, order.duration_months,
                         order_no, "SIMULATE_" + order_no, db)
    await db.commit()
    return {"message": "模拟支付成功"}


@router.get("/config")
async def get_payment_config(current_user=Depends(require_admin)):
    """Admin: get payment config (masks sensitive keys)."""
    config = ps.load_config()
    # Mask keys for display
    def mask(s: str) -> str:
        if not s:
            return ""
        return s[:4] + "****" + s[-4:] if len(s) > 8 else "****"

    safe = {
        "pricing": config["pricing"],
        "wechat": {**config["wechat"], "private_key": mask(config["wechat"].get("private_key", "")),
                   "apiv3_key": mask(config["wechat"].get("apiv3_key", ""))},
        "alipay": {**config["alipay"],
                   "private_key": mask(config["alipay"].get("private_key", "")),
                   "alipay_public_key": mask(config["alipay"].get("alipay_public_key", "")),
                   "app_cert": mask(config["alipay"].get("app_cert", "")),
                   "alipay_cert": mask(config["alipay"].get("alipay_cert", "")),
                   "alipay_root_cert": mask(config["alipay"].get("alipay_root_cert", ""))},
    }
    return safe


@router.put("/config")
async def update_payment_config(
    data: PaymentConfigUpdate,
    current_user=Depends(require_admin),
):
    """Admin: update payment config. Only updates provided fields."""
    config = ps.load_config()
    if data.pricing:
        config["pricing"].update(data.pricing)
    if data.wechat:
        for k, v in data.wechat.items():
            if v is None:
                continue
            if isinstance(v, str) and "****" in v:
                continue  # 脱敏占位符，跳过
            config["wechat"][k] = v
    if data.alipay:
        for k, v in data.alipay.items():
            if v is None:
                continue
            if isinstance(v, str) and "****" in v:
                continue  # 脱敏占位符，跳过
            config["alipay"][k] = v
    ps.save_config(config)
    return {"message": "配置已保存"}
