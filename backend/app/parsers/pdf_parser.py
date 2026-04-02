"""Parser for PDF files.

优先级：
1. 百度 OCR（配置了 Key 时）
2. PyPDF2 文字层提取
3. pymupdf + Tesseract OCR 兜底
"""

from typing import List
from PyPDF2 import PdfReader
from app.parsers.base_parser import BaseParser, ParsedChunk


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
            from app.services.baidu_ocr import load_baidu_config, ocr_general, ocr_business_license
            import fitz
            import io

            config = load_baidu_config()
            api_key = config.get("api_key", "")
            secret_key = config.get("secret_key", "")
            if not api_key or not secret_key:
                return []

            doc = fitz.open(file_path)
            chunks = []
            total = len(doc)
            is_license = any(kw in filename for kw in ["营业执照", "执照", "license"])

            for page_num in range(total):
                page = doc[page_num]
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                image_bytes = pix.tobytes("png")

                if is_license and page_num == 0:
                    text = ocr_business_license(image_bytes, api_key, secret_key)
                else:
                    text = ocr_general(image_bytes, api_key, secret_key)

                if text and text.strip():
                    chunks.append(ParsedChunk(
                        text=text.strip(),
                        metadata={"source": filename, "file_type": "pdf",
                                  "page_number": page_num + 1, "total_pages": total,
                                  "ocr_engine": "baidu"},
                        page_number=page_num + 1,
                    ))
            doc.close()
            return chunks
        except Exception:
            return []

    # ── PyPDF2 文字层 ─────────────────────────────────────────
    def _extract_text(self, file_path: str, filename: str) -> List[ParsedChunk]:
        try:
            reader = PdfReader(file_path)
            chunks = []
            total = len(reader.pages)
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
        except Exception:
            return []

    # ── Tesseract OCR 兜底 ────────────────────────────────────
    def _extract_tesseract(self, file_path: str, filename: str) -> List[ParsedChunk]:
        try:
            import fitz
            import pytesseract
            from PIL import Image
            import io

            doc = fitz.open(file_path)
            chunks = []
            total = len(doc)
            for page_num in range(total):
                page = doc[page_num]
                mat = fitz.Matrix(3.0, 3.0)
                pix = page.get_pixmap(matrix=mat)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
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
        except Exception:
            return []
