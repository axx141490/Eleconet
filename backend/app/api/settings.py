"""Model configuration API endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.security import get_current_user
from app.models.user import User
from app.services.llm_provider import (
    load_model_config, save_model_config, PROVIDER_PRESETS
)

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
    current_user: User = Depends(get_current_user),
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
