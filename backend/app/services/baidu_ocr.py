"""百度 OCR 服务封装（通用文字识别 + 营业执照结构化识别）。"""

import base64
import json
import os
import requests
from typing import Optional

BAIDU_OCR_CONFIG_FILE = "./data/baidu_ocr_config.json"
_TOKEN_CACHE: dict = {}


def load_baidu_config() -> dict:
    if os.path.exists(BAIDU_OCR_CONFIG_FILE):
        try:
            with open(BAIDU_OCR_CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"api_key": "", "secret_key": "", "enabled": False}


def save_baidu_config(config: dict):
    os.makedirs("./data", exist_ok=True)
    with open(BAIDU_OCR_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def _get_access_token(api_key: str, secret_key: str) -> str:
    cache_key = f"{api_key}:{secret_key}"
    if cache_key in _TOKEN_CACHE:
        return _TOKEN_CACHE[cache_key]

    url = "https://aip.baidubce.com/oauth/2.0/token"
    resp = requests.post(url, params={
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key,
    }, timeout=10)
    resp.raise_for_status()
    token = resp.json()["access_token"]
    _TOKEN_CACHE[cache_key] = token
    return token


def _image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def ocr_general(image_bytes: bytes, api_key: str, secret_key: str) -> str:
    """通用文字识别（高精度版），返回识别文本。"""
    token = _get_access_token(api_key, secret_key)
    url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={token}"
    resp = requests.post(url, data={
        "image": _image_to_base64(image_bytes),
        "language_type": "CHN_ENG",
        "detect_direction": "true",
    }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    if "words_result" not in result:
        raise RuntimeError(f"百度 OCR 错误: {result}")
    return "\n".join(item["words"] for item in result["words_result"])


def ocr_business_license(image_bytes: bytes, api_key: str, secret_key: str) -> str:
    """营业执照识别，返回结构化文本。"""
    token = _get_access_token(api_key, secret_key)
    url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/business_license?access_token={token}"
    resp = requests.post(url, data={
        "image": _image_to_base64(image_bytes),
    }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    if "words_result" not in result:
        raise RuntimeError(f"百度营业执照 OCR 错误: {result}")

    fields = result["words_result"]
    lines = []
    for key, val in fields.items():
        word = val.get("words", "").strip()
        if word:
            lines.append(f"{key}：{word}")
    return "\n".join(lines)
