"""Payment service — WeChat Pay v3 + Alipay integration."""

import json
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

CONFIG_PATH = "./data/payment_config.json"

DEFAULT_CONFIG = {
    "pricing": {
        "pro_monthly": 2900,        # ¥29
        "pro_yearly": 19900,        # ¥199
        "enterprise_monthly": 9900, # ¥99
        "enterprise_yearly": 69900, # ¥699
    },
    "wechat": {
        "enabled": False,
        "appid": "",
        "mchid": "",
        "private_key": "",
        "cert_serial_no": "",
        "apiv3_key": "",
        "notify_url": "",
    },
    "alipay": {
        "enabled": False,
        "sandbox": False,
        "cert_mode": True,          # True=证书验证，False=公钥验证
        "app_id": "",
        "private_key": "",
        # 证书模式（cert_mode=True）所需，填证书文件内容（PEM 格式）
        "app_cert": "",             # 应用公钥证书 appCertPublicKey_xxx.crt
        "alipay_root_cert": "",     # 支付宝根证书 alipayRootCert.crt
        "alipay_cert": "",          # 支付宝公钥证书 alipayCertPublicKey_RSA2.crt
        # 公钥模式（cert_mode=False）所需
        "alipay_public_key": "",
        "notify_url": "",
        "return_url": "",
    },
}


def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                saved = json.load(f)
            # Merge with defaults to handle missing keys
            config = json.loads(json.dumps(DEFAULT_CONFIG))
            for k in config:
                if k in saved:
                    if isinstance(config[k], dict):
                        config[k].update(saved[k])
                    else:
                        config[k] = saved[k]
            return config
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(config: Dict[str, Any]):
    os.makedirs("./data", exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_price(tier: str, duration_months: int) -> int:
    """Return price in 分."""
    config = load_config()
    pricing = config["pricing"]
    key = f"{tier}_{'yearly' if duration_months == 12 else 'monthly'}"
    return pricing.get(key, 0)


def _normalize_private_key(key: str) -> str:
    """Ensure RSA private key has proper PEM headers for python-alipay-sdk."""
    key = key.strip()
    # Already has headers — return as-is
    if key.startswith("-----"):
        return key
    # Raw base64 content — wrap with PKCS#8 header (Alipay key tool default)
    body = key.replace("\n", "").replace("\r", "").replace(" ", "")
    # Re-wrap to 64-char lines
    lines = [body[i:i+64] for i in range(0, len(body), 64)]
    return "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END PRIVATE KEY-----"


def _normalize_public_key(key: str) -> str:
    """Ensure Alipay public key has proper PEM headers."""
    key = key.strip()
    if key.startswith("-----"):
        return key
    body = key.replace("\n", "").replace("\r", "").replace(" ", "")
    lines = [body[i:i+64] for i in range(0, len(body), 64)]
    return "-----BEGIN PUBLIC KEY-----\n" + "\n".join(lines) + "\n-----END PUBLIC KEY-----"


def make_order_no() -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:8].upper()
    return f"RAG{ts}{uid}"


def _normalize_wechat_private_key(key: str) -> str:
    """Normalize WeChat private key to valid PEM regardless of how it was pasted."""
    key = key.strip()
    if "BEGIN RSA PRIVATE KEY" in key:
        header, footer = "-----BEGIN RSA PRIVATE KEY-----", "-----END RSA PRIVATE KEY-----"
    else:
        header, footer = "-----BEGIN PRIVATE KEY-----", "-----END PRIVATE KEY-----"
    # Remove all header/footer markers then strip every whitespace character from the body.
    # This handles keys pasted as a single space-separated line or with mixed line endings.
    body = re.sub(r"-----[^-]+-----", "", key)
    body = re.sub(r"\s+", "", body)
    wrapped = "\n".join(body[i:i + 64] for i in range(0, len(body), 64))
    return f"{header}\n{wrapped}\n{footer}"


# ── WeChat Pay ─────────────────────────────────────────────────────────────

_WECHAT_REQUIRED = ("appid", "mchid", "private_key", "cert_serial_no", "apiv3_key", "notify_url")


def _wechat_config_valid(wcfg: dict) -> bool:
    missing = [k for k in _WECHAT_REQUIRED if not wcfg.get(k, "").strip()]
    if missing:
        print(f"WeChat pay config incomplete, missing fields: {missing}")
        return False
    return True


async def wechat_create_native(order_no: str, amount_fen: int, tier: str, duration_months: int) -> Optional[str]:
    """Create WeChat native pay order, return code_url for QR display."""
    config = load_config()
    wcfg = config["wechat"]
    if not wcfg.get("enabled"):
        return None
    if not _wechat_config_valid(wcfg):
        return None

    try:
        from wechatpayv3 import WeChatPay, WeChatPayType
        wx = WeChatPay(
            wechatpay_type=WeChatPayType.NATIVE,
            mchid=wcfg["mchid"],
            private_key=_normalize_wechat_private_key(wcfg["private_key"]),
            cert_serial_no=wcfg["cert_serial_no"],
            apiv3_key=wcfg["apiv3_key"],
            appid=wcfg["appid"],
            notify_url=wcfg.get("notify_url", ""),
        )
        label = "Pro" if tier == "pro" else "Enterprise"
        dur = "年" if duration_months == 12 else "月"
        code, message = wx.pay(
            description=f"RAG知识库 {label} 套餐（{duration_months}{dur}）",
            out_trade_no=order_no,
            amount={"total": amount_fen},
        )
        if code == 200 and isinstance(message, dict):
            return message.get("code_url")
        print(f"WeChat pay non-200 response: code={code}, message={message}")
    except ImportError:
        pass
    except Exception as e:
        print(f"WeChat pay error: {e}")
    return None


async def wechat_query_order(order_no: str) -> Optional[str]:
    """Query WeChat order status. Returns 'paid', 'pending', or None on error."""
    config = load_config()
    wcfg = config["wechat"]
    if not wcfg.get("enabled"):
        return None
    if not _wechat_config_valid(wcfg):
        return None
    try:
        from wechatpayv3 import WeChatPay, WeChatPayType
        wx = WeChatPay(
            wechatpay_type=WeChatPayType.NATIVE,
            mchid=wcfg["mchid"],
            private_key=_normalize_wechat_private_key(wcfg["private_key"]),
            cert_serial_no=wcfg["cert_serial_no"],
            apiv3_key=wcfg["apiv3_key"],
            appid=wcfg["appid"],
            notify_url=wcfg.get("notify_url", ""),
        )
        code, message = wx.query(out_trade_no=order_no)
        if code == 200 and isinstance(message, dict):
            trade_state = message.get("trade_state", "")
            if trade_state == "SUCCESS":
                return "paid"
            return "pending"
    except ImportError:
        pass
    except Exception as e:
        print(f"WeChat query error: {e}")
    return None


def wechat_verify_callback(headers: dict, body: bytes) -> Optional[Dict]:
    """Verify WeChat callback signature and decrypt. Returns order dict or None."""
    config = load_config()
    wcfg = config["wechat"]
    if not wcfg.get("enabled"):
        return None
    if not _wechat_config_valid(wcfg):
        return None
    try:
        from wechatpayv3 import WeChatPay, WeChatPayType
        wx = WeChatPay(
            wechatpay_type=WeChatPayType.NATIVE,
            mchid=wcfg["mchid"],
            private_key=_normalize_wechat_private_key(wcfg["private_key"]),
            cert_serial_no=wcfg["cert_serial_no"],
            apiv3_key=wcfg["apiv3_key"],
            appid=wcfg["appid"],
            notify_url=wcfg.get("notify_url", ""),
        )
        result = wx.callback(headers=headers, body=body)
        if result and result.get("event_type") == "TRANSACTION.SUCCESS":
            return result.get("resource", {})
    except ImportError:
        pass
    except Exception as e:
        print(f"WeChat callback verify error: {e}")
    return None


# ── Alipay ────────────────────────────────────────────────────────────────

def _build_alipay(acfg: dict):
    """Build AliPay instance supporting both cert mode and public key mode."""
    from alipay import AliPay, DCAliPay
    private_key = _normalize_private_key(acfg["private_key"])
    sandbox = acfg.get("sandbox", False)

    if acfg.get("cert_mode", True):
        # 证书验证模式
        return DCAliPay(
            appid=acfg["app_id"],
            app_notify_url=acfg.get("notify_url", ""),
            app_private_key_string=private_key,
            app_public_key_cert_string=acfg.get("app_cert", ""),
            alipay_public_key_cert_string=acfg.get("alipay_cert", ""),
            alipay_root_cert_string=acfg.get("alipay_root_cert", ""),
            debug=sandbox,
        )
    else:
        # 公钥验证模式
        return AliPay(
            appid=acfg["app_id"],
            app_notify_url=acfg.get("notify_url", ""),
            app_private_key_string=private_key,
            alipay_public_key_string=_normalize_public_key(acfg.get("alipay_public_key", "")),
            sign_type="RSA2",
            debug=sandbox,
        )


async def alipay_create_order(order_no: str, amount_fen: int, tier: str, duration_months: int) -> Optional[str]:
    """Create Alipay PC web pay order. Returns redirect URL string."""
    config = load_config()
    acfg = config["alipay"]
    if not acfg.get("enabled"):
        return None
    amount_yuan = f"{amount_fen / 100:.2f}"
    label = "Pro" if tier == "pro" else "Enterprise"
    dur = "年" if duration_months == 12 else "月"
    subject = f"RAG知识库 {label} 套餐（{duration_months}{dur}）"
    try:
        ap = _build_alipay(acfg)
        order_string = ap.api_alipay_trade_page_pay(
            subject=subject,
            out_trade_no=order_no,
            total_amount=amount_yuan,
            return_url=acfg.get("return_url", ""),
            notify_url=acfg.get("notify_url", ""),
        )
        gateway = "https://openapi-sandbox.dl.alipaydev.com/gateway.do" if acfg.get("sandbox") else "https://openapi.alipay.com/gateway.do"
        return f"{gateway}?{order_string}"
    except ImportError:
        pass
    except Exception as e:
        print(f"Alipay create error: {e}")
    return None


async def alipay_query_order(order_no: str) -> Optional[str]:
    """Query Alipay order status. Returns 'paid', 'pending', or None."""
    config = load_config()
    acfg = config["alipay"]
    if not acfg.get("enabled"):
        return None
    try:
        ap = _build_alipay(acfg)
        result = ap.api_alipay_trade_query(out_trade_no=order_no)
        if result.get("trade_status") == "TRADE_SUCCESS":
            return "paid"
        return "pending"
    except ImportError:
        pass
    except Exception as e:
        print(f"Alipay query error: {e}")
    return None


def alipay_verify_callback(data: dict) -> bool:
    """Verify Alipay async notification signature."""
    config = load_config()
    acfg = config["alipay"]
    if not acfg.get("enabled"):
        return False
    try:
        ap = _build_alipay(acfg)
        sign = data.pop("sign", None)
        data.pop("sign_type", None)
        return ap.verify(data, sign)
    except ImportError:
        return False
    except Exception:
        return False
