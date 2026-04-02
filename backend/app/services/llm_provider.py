"""LLM & Embedding provider abstraction supporting multiple backends."""

import json
import os
from typing import Dict

from openai import OpenAI

CONFIG_FILE = "./data/model_config.json"

# Preset defaults per provider
PROVIDER_PRESETS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "chat_model": "gpt-4o-mini",
        "embedding_model": "text-embedding-3-small",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "chat_model": "deepseek-chat",
        "embedding_model": "",  # DeepSeek has no embedding API
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "chat_model": "glm-4-flash",
        "embedding_model": "embedding-3",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "chat_model": "qwen-plus",
        "embedding_model": "text-embedding-v3",
    },
    "ollama": {
        "base_url": "http://host.docker.internal:11434/v1",
        "chat_model": "qwen2.5:7b",
        "embedding_model": "nomic-embed-text",
    },
    "custom": {
        "base_url": "",
        "chat_model": "",
        "embedding_model": "",
    },
}

DEFAULT_CONFIG = {
    "llm": {
        "provider": "openai",
        "api_key": "",
        "base_url": "",
        "model": "gpt-4o-mini",
    },
    "embedding": {
        "provider": "openai",
        "api_key": "",
        "base_url": "",
        "model": "text-embedding-3-small",
    },
}


def load_model_config() -> Dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_model_config(config: Dict):
    os.makedirs("./data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def _resolve_base_url(provider: str, base_url: str) -> str:
    if base_url:
        return base_url
    return PROVIDER_PRESETS.get(provider, {}).get("base_url", "")


def get_llm_client() -> OpenAI:
    config = load_model_config()
    llm = config["llm"]
    provider = llm.get("provider", "openai")
    api_key = llm.get("api_key", "") or "dummy"
    base_url = _resolve_base_url(provider, llm.get("base_url", "")) or None

    if provider == "ollama":
        api_key = "ollama"

    return OpenAI(api_key=api_key, base_url=base_url)


def get_llm_model() -> str:
    config = load_model_config()
    return config["llm"].get("model", "gpt-4o-mini")


def get_embedding_function():
    config = load_model_config()
    emb = config["embedding"]
    provider = emb.get("provider", "openai")
    api_key = emb.get("api_key", "") or "dummy"
    base_url = _resolve_base_url(provider, emb.get("base_url", ""))
    model = emb.get("model", "text-embedding-3-small")

    if provider == "ollama":
        from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
        ollama_base = base_url or "http://host.docker.internal:11434"
        return OllamaEmbeddingFunction(
            url=f"{ollama_base}/api/embeddings",
            model_name=model or "nomic-embed-text",
        )
    else:
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
        kwargs = {
            "api_key": api_key,
            "model_name": model or "text-embedding-3-small",
        }
        if base_url:
            kwargs["api_base"] = base_url
        return OpenAIEmbeddingFunction(**kwargs)
