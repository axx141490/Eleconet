"""Payment order model."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tier = Column(String(20), nullable=False)            # pro / enterprise
    duration_months = Column(Integer, nullable=False)   # 1 or 12
    amount_fen = Column(Integer, nullable=False)         # amount in 分 (¥29.00 = 2900)
    pay_method = Column(String(20), nullable=False)      # wechat / alipay
    status = Column(String(20), default="pending", nullable=False)  # pending/paid/expired
    trade_no = Column(String(128), nullable=True)        # third-party trade number
    qr_code_url = Column(Text, nullable=True)            # wechat code_url / alipay url
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)         # tier expiry after payment

    user = relationship("User", backref="payment_orders")
