"""Model configuration API endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.services.llm_provider import (
    load_model_config, save_model_config, PROVIDER_PRESETS
)
from app.services.baidu_ocr import load_baidu_config, save_baidu_config
from app.services.sms_service import load_sms_config, save_sms_config

router = APIRouter(prefix="/api/settings", tags=["Settings"])


class ProviderConfig(BaseModel):
    provider: str
    api_key: Optional[str] = ""
    base_url: Optional[str] = ""
    model: str


class ModelConfig(BaseModel):
    llm: ProviderConfig
    embedding: ProviderConfig


def _mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return key
    return key[:4] + "****" + key[-4:]


@router.get("/model")
async def get_model_config(current_user: User = Depends(get_current_user)):
    config = load_model_config()
    # Mask API keys in response
    masked = {
        "llm": {**config["llm"], "api_key": _mask_key(config["llm"].get("api_key", ""))},
        "embedding": {**config["embedding"], "api_key": _mask_key(config["embedding"].get("api_key", ""))},
    }
    return masked


@router.put("/model")
async def update_model_config(
    data: ModelConfig,
    current_user=Depends(require_admin),
):
    current = load_model_config()

    def merge_key(new_key: str, old_key: str) -> str:
        # If key contains ****, keep the old key
        if new_key and "****" not in new_key:
            return new_key
        return old_key

    config = {
        "llm": {
            "provider": data.llm.provider,
            "api_key": merge_key(data.llm.api_key or "", current["llm"].get("api_key", "")),
            "base_url": data.llm.base_url or "",
            "model": data.llm.model,
        },
        "embedding": {
            "provider": data.embedding.provider,
            "api_key": merge_key(data.embedding.api_key or "", current["embedding"].get("api_key", "")),
            "base_url": data.embedding.base_url or "",
            "model": data.embedding.model,
        },
    }
    save_model_config(config)
    return {"message": "配置已保存"}


@router.get("/providers")
async def get_providers(current_user: User = Depends(get_current_user)):
    return PROVIDER_PRESETS


class BaiduOCRConfig(BaseModel):
    api_key: Optional[str] = ""
    secret_key: Optional[str] = ""
    enabled: bool = False


@router.get("/baidu-ocr")
async def get_baidu_ocr_config(current_user: User = Depends(get_current_user)):
    config = load_baidu_config()
    return {
        "api_key": _mask_key(config.get("api_key", "")),
        "secret_key": _mask_key(config.get("secret_key", "")),
        "enabled": config.get("enabled", False),
    }


@router.put("/baidu-ocr")
async def update_baidu_ocr_config(
    data: BaiduOCRConfig,
    current_user=Depends(require_admin),
):
    current = load_baidu_config()

    def merge_key(new_key: str, old_key: str) -> str:
        if new_key and "****" not in new_key:
            return new_key
        return old_key

    save_baidu_config({
        "api_key": merge_key(data.api_key or "", current.get("api_key", "")),
        "secret_key": merge_key(data.secret_key or "", current.get("secret_key", "")),
        "enabled": data.enabled,
    })
    return {"message": "百度 OCR 配置已保存"}


# ─── SMS Config ──────────────────────────────────────

class SmsProviderAliyun(BaseModel):
    access_key_id: Optional[str] = ""
    access_key_secret: Optional[str] = ""
    sign_name: Optional[str] = ""
    template_code: Optional[str] = ""


class SmsProviderTencent(BaseModel):
    secret_id: Optional[str] = ""
    secret_key: Optional[str] = ""
    app_id: Optional[str] = ""
    sign_name: Optional[str] = ""
    template_id: Optional[str] = ""


class SmsConfig(BaseModel):
    enabled: bool = False
    require_phone_on_register: bool = False
    provider: str = "aliyun"
    aliyun: Optional[SmsProviderAliyun] = None
    tencent: Optional[SmsProviderTencent] = None


@router.get("/sms")
async def get_sms_config(current_user=Depends(require_admin)):
    config = load_sms_config()

    def mask(s: str) -> str:
        if not s or len(s) < 8:
            return s
        return s[:4] + "****" + s[-4:]

    return {
        "enabled": config["enabled"],
        "require_phone_on_register": config["require_phone_on_register"],
        "provider": config["provider"],
        "aliyun": {
            "access_key_id": mask(config["aliyun"].get("access_key_id", "")),
            "access_key_secret": mask(config["aliyun"].get("access_key_secret", "")),
            "sign_name": config["aliyun"].get("sign_name", ""),
            "template_code": config["aliyun"].get("template_code", ""),
        },
        "tencent": {
            "secret_id": mask(config["tencent"].get("secret_id", "")),
            "secret_key": mask(config["tencent"].get("secret_key", "")),
            "app_id": config["tencent"].get("app_id", ""),
            "sign_name": config["tencent"].get("sign_name", ""),
            "template_id": config["tencent"].get("template_id", ""),
        },
    }


@router.put("/sms")
async def update_sms_config(data: SmsConfig, current_user=Depends(require_admin)):
    current = load_sms_config()

    def merge(new_val: str, old_val: str) -> str:
        if new_val and "****" not in new_val:
            return new_val
        return old_val

    current["enabled"] = data.enabled
    current["require_phone_on_register"] = data.require_phone_on_register
    current["provider"] = data.provider

    if data.aliyun:
        al = data.aliyun
        current["aliyun"]["access_key_id"] = merge(al.access_key_id or "", current["aliyun"]["access_key_id"])
        current["aliyun"]["access_key_secret"] = merge(al.access_key_secret or "", current["aliyun"]["access_key_secret"])
        current["aliyun"]["sign_name"] = al.sign_name or current["aliyun"]["sign_name"]
        current["aliyun"]["template_code"] = al.template_code or current["aliyun"]["template_code"]

    if data.tencent:
        tc = data.tencent
        current["tencent"]["secret_id"] = merge(tc.secret_id or "", current["tencent"]["secret_id"])
        current["tencent"]["secret_key"] = merge(tc.secret_key or "", current["tencent"]["secret_key"])
        current["tencent"]["app_id"] = tc.app_id or current["tencent"]["app_id"]
        current["tencent"]["sign_name"] = tc.sign_name or current["tencent"]["sign_name"]
        current["tencent"]["template_id"] = tc.template_id or current["tencent"]["template_id"]

    save_sms_config(current)
    return {"message": "短信配置已保存"}


@router.get("/sms/status")
async def get_sms_status():
    """Public: returns whether SMS is enabled and phone is required on register."""
    config = load_sms_config()
    return {
        "enabled": config.get("enabled", False),
        "require_phone_on_register": config.get("require_phone_on_register", False),
    }
