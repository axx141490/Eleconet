"""Parser for image files.

优先级：
1. 百度 OCR（配置且启用时）
2. Tesseract OCR 兜底
"""

from typing import List
from app.parsers.base_parser import BaseParser, ParsedChunk


class ImageParser(BaseParser):

    @staticmethod
    def supported_extensions() -> List[str]:
        return [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]

    async def parse(self, file_path: str, filename: str) -> List[ParsedChunk]:
        text = self._extract_baidu(file_path) or self._extract_tesseract(file_path)

        if not text:
            text = f"[图片文件: {filename} - 无法提取文字]"

        return [ParsedChunk(
            text=text,
            metadata={"source": filename, "file_type": "image"},
        )]

    def _extract_baidu(self, file_path: str) -> str:
        try:
            from app.services.baidu_ocr import load_baidu_config, ocr_general
            config = load_baidu_config()
            if not config.get("enabled", False):
                return ""
            api_key = config.get("api_key", "")
            secret_key = config.get("secret_key", "")
            if not api_key or not secret_key:
                return ""
            with open(file_path, "rb") as f:
                return ocr_general(f.read(), api_key, secret_key)
        except Exception:
            return ""

    def _extract_tesseract(self, file_path: str) -> str:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(file_path)
            return pytesseract.image_to_string(img, lang="chi_sim+eng").strip()
        except Exception:
            return ""
