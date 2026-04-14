"""SMS service — send verification codes via Aliyun or Tencent Cloud."""

import json
import os
import random
import time
from typing import Dict, Tuple

CONFIG_PATH = "./data/sms_config.json"

DEFAULT_CONFIG = {
    "enabled": False,
    "require_phone_on_register": False,
    "provider": "aliyun",   # aliyun | tencent
    "aliyun": {
        "access_key_id": "",
        "access_key_secret": "",
        "sign_name": "",
        "template_code": "",
    },
    "tencent": {
        "secret_id": "",
        "secret_key": "",
        "app_id": "",
        "sign_name": "",
        "template_id": "",
    },
}

# In-memory: phone -> (code, expire_timestamp)
_code_store: Dict[str, Tuple[str, float]] = {}
CODE_TTL = 300   # 5 分钟有效
SEND_COOLDOWN = 60  # 同一号码 60 秒内不可重复发送
_last_sent: Dict[str, float] = {}

# 验证失败次数限制：phone -> (失败次数, 锁定到期时间)
_verify_failures: Dict[str, Tuple[int, float]] = {}
MAX_VERIFY_ATTEMPTS = 5   # 最多失败 5 次
VERIFY_LOCKOUT = 600      # 锁定 10 分钟


def load_sms_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                saved = json.load(f)
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


def save_sms_config(config: dict):
    os.makedirs("./data", exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def _generate_code() -> str:
    return str(random.randint(100000, 999999))


def check_cooldown(phone: str):
    last = _last_sent.get(phone, 0)
    if time.time() - last < SEND_COOLDOWN:
        remaining = int(SEND_COOLDOWN - (time.time() - last))
        raise RuntimeError(f"发送过于频繁，请 {remaining} 秒后再试")


def verify_code(phone: str, code: str) -> bool:
    now = time.time()

    # 检查是否被锁定
    failures, locked_until = _verify_failures.get(phone, (0, 0))
    if locked_until > now:
        remaining = int(locked_until - now)
        raise RuntimeError(f"验证码错误次数过多，请 {remaining} 秒后再试")

    entry = _code_store.get(phone)
    if not entry:
        return False
    stored_code, expire_at = entry
    if now > expire_at:
        _code_store.pop(phone, None)
        return False
    if stored_code != code:
        # 累计失败次数
        failures += 1
        if failures >= MAX_VERIFY_ATTEMPTS:
            _verify_failures[phone] = (failures, now + VERIFY_LOCKOUT)
        else:
            _verify_failures[phone] = (failures, 0)
        return False

    # 验证成功，清除记录
    _code_store.pop(phone, None)
    _verify_failures.pop(phone, None)
    return True


def send_sms_code(phone: str):
    """Generate and send a 6-digit verification code to the given phone number."""
    config = load_sms_config()
    if not config.get("enabled"):
        raise RuntimeError("短信服务未启用")

    check_cooldown(phone)

    code = _generate_code()
    _code_store[phone] = (code, time.time() + CODE_TTL)
    _last_sent[phone] = time.time()

    provider = config.get("provider", "aliyun")
    if provider == "aliyun":
        _send_aliyun(phone, code, config["aliyun"])
    elif provider == "tencent":
        _send_tencent(phone, code, config["tencent"])
    else:
        raise RuntimeError(f"不支持的短信服务商: {provider}")


def _send_aliyun(phone: str, code: str, cfg: dict):
    try:
        from alibabacloud_dysmsapi20170525.client import Client
        from alibabacloud_tea_openapi.models import Config
        from alibabacloud_dysmsapi20170525 import models as sms_models

        client = Client(Config(
            access_key_id=cfg["access_key_id"],
            access_key_secret=cfg["access_key_secret"],
            endpoint="dysmsapi.aliyuncs.com",
        ))
        req = sms_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name=cfg["sign_name"],
            template_code=cfg["template_code"],
            template_param=json.dumps({"code": code}),
        )
        resp = client.send_sms(req)
        if resp.body.code != "OK":
            raise RuntimeError(f"阿里云短信发送失败: {resp.body.message}")
    except ImportError:
        raise RuntimeError("请安装阿里云短信 SDK: pip install alibabacloud-dysmsapi20170525")


def _send_tencent(phone: str, code: str, cfg: dict):
    try:
        from tencentcloud.common import credential
        from tencentcloud.sms.v20210111 import sms_client, models as sms_models

        cred = credential.Credential(cfg["secret_id"], cfg["secret_key"])
        client = sms_client.SmsClient(cred, "ap-guangzhou")
        req = sms_models.SendSmsRequest()
        req.SmsSdkAppId = cfg["app_id"]
        req.SignName = cfg["sign_name"]
        req.TemplateId = cfg["template_id"]
        req.TemplateParamSet = [code]
        req.PhoneNumberSet = [f"+86{phone}"]
        resp = client.SendSms(req)
        if resp.SendStatusSet[0].Code != "Ok":
            raise RuntimeError(f"腾讯云短信发送失败: {resp.SendStatusSet[0].Message}")
    except ImportError:
        raise RuntimeError("请安装腾讯云短信 SDK: pip install tencentcloud-sdk-python-sms")
