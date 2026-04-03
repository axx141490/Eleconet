"""Parser for PDF files.

优先级：
1. 百度 OCR（配置了 Key 时）
2. PyPDF2 文字层提取
3. pymupdf + Tesseract OCR 兜底
"""

import io
import logging
import time
from typing import List

from PyPDF2 import PdfReader

from app.parsers.base_parser import BaseParser, ParsedChunk

logger = logging.getLogger(__name__)

# 百度 OCR QPS 限制（免费版 QPS=2，留余量用 0.6s 间隔）
_BAIDU_QPS_INTERVAL = 0.6
# QPS 超限时的重试配置
_BAIDU_RETRY_TIMES = 3
_BAIDU_RETRY_WAIT = 2.0


class PDFParser(BaseParser):

    @staticmethod
    def supported_extensions() -> List[str]:
        return [".pdf"]

    async def parse(self, file_path: str, filename: str) -> List[ParsedChunk]:
        # 1. 百度 OCR（优先）
        chunks = self._extract_baidu(file_path, filename)
        if chunks:
            return chunks

        # 2. PyPDF2 文字层
        chunks = self._extract_text(file_path, filename)
        if chunks:
            return chunks

        # 3. Tesseract OCR 兜底
        return self._extract_tesseract(file_path, filename)

    # ── 百度 OCR ─────────────────────────────────────────────
    def _extract_baidu(self, file_path: str, filename: str) -> List[ParsedChunk]:
        try:
            import fitz
            from app.services.baidu_ocr import load_baidu_config, ocr_general, ocr_business_license

            config = load_baidu_config()
            if not config.get("enabled", False):
                return []
            api_key    = config.get("api_key", "")
            secret_key = config.get("secret_key", "")
            if not api_key or not secret_key:
                return []

            doc = fitz.open(file_path)
            total = len(doc)
            chunks = []
            is_license = any(kw in filename for kw in ["营业执照", "执照", "license"])

            logger.info(f"百度 OCR 开始处理 {filename}，共 {total} 页")

            for page_num in range(total):
                page = doc[page_num]
                mat  = fitz.Matrix(2.0, 2.0)
                pix  = page.get_pixmap(matrix=mat)
                image_bytes = pix.tobytes("png")

                text = self._baidu_ocr_with_retry(
                    image_bytes, api_key, secret_key,
                    is_license=(is_license and page_num == 0),
                    page_num=page_num, filename=filename,
                )

                if text and text.strip():
                    chunks.append(ParsedChunk(
                        text=text.strip(),
                        metadata={
                            "source": filename, "file_type": "pdf",
                            "page_number": page_num + 1, "total_pages": total,
                            "ocr_engine": "baidu",
                        },
                        page_number=page_num + 1,
                    ))

                # QPS 限速：每页请求后等待，避免超限
                if page_num < total - 1:
                    time.sleep(_BAIDU_QPS_INTERVAL)

            doc.close()
            logger.info(f"百度 OCR 完成 {filename}：提取 {len(chunks)}/{total} 页")
            return chunks

        except Exception as e:
            logger.warning(f"百度 OCR 处理 {filename} 失败：{e}")
            return []

    def _baidu_ocr_with_retry(
        self,
        image_bytes: bytes,
        api_key: str,
        secret_key: str,
        is_license: bool,
        page_num: int,
        filename: str,
    ) -> str:
        """调用百度 OCR，遇到 QPS 超限（error_code=18）时自动重试。"""
        from app.services.baidu_ocr import ocr_general, ocr_business_license
        import requests

        for attempt in range(1, _BAIDU_RETRY_TIMES + 1):
            try:
                if is_license:
                    return ocr_business_license(image_bytes, api_key, secret_key)
                else:
                    return ocr_general(image_bytes, api_key, secret_key)

            except RuntimeError as e:
                err_str = str(e)
                # 百度 QPS 超限 error_code=18
                if "18" in err_str or "Open api qps" in err_str or "QPS" in err_str.upper():
                    wait = _BAIDU_RETRY_WAIT * attempt
                    logger.warning(
                        f"百度 OCR QPS 超限（第 {attempt} 次），{filename} 第 {page_num+1} 页，"
                        f"{wait:.1f}s 后重试"
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"百度 OCR 错误（{filename} 第 {page_num+1} 页）：{e}")
                    return ""

            except Exception as e:
                logger.error(f"百度 OCR 异常（{filename} 第 {page_num+1} 页，第 {attempt} 次）：{e}")
                if attempt < _BAIDU_RETRY_TIMES:
                    time.sleep(_BAIDU_RETRY_WAIT)
                else:
                    return ""

        logger.error(f"百度 OCR 重试耗尽（{filename} 第 {page_num+1} 页）")
        return ""

    # ── PyPDF2 文字层 ─────────────────────────────────────────
    def _extract_text(self, file_path: str, filename: str) -> List[ParsedChunk]:
        try:
            reader = PdfReader(file_path)
            chunks = []
            total  = len(reader.pages)
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    chunks.append(ParsedChunk(
                        text=text.strip(),
                        metadata={"source": filename, "file_type": "pdf",
                                  "page_number": page_num, "total_pages": total},
                        page_number=page_num,
                    ))
            return chunks
        except Exception as e:
            logger.warning(f"PyPDF2 提取 {filename} 失败：{e}")
            return []

    # ── Tesseract OCR 兜底 ────────────────────────────────────
    def _extract_tesseract(self, file_path: str, filename: str) -> List[ParsedChunk]:
        try:
            import fitz
            import pytesseract
            from PIL import Image

            doc    = fitz.open(file_path)
            chunks = []
            total  = len(doc)
            for page_num in range(total):
                page = doc[page_num]
                mat  = fitz.Matrix(3.0, 3.0)
                pix  = page.get_pixmap(matrix=mat)
                img  = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img, lang="chi_sim+eng")
                if text and text.strip():
                    chunks.append(ParsedChunk(
                        text=text.strip(),
                        metadata={"source": filename, "file_type": "pdf",
                                  "page_number": page_num + 1, "total_pages": total,
                                  "ocr_engine": "tesseract"},
                        page_number=page_num + 1,
                    ))
            doc.close()
            return chunks
        except Exception as e:
            logger.warning(f"Tesseract OCR 处理 {filename} 失败：{e}")
            return []
