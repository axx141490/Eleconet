"""Parser for PDF files — text layer first, OCR fallback for scanned PDFs."""

from typing import List
from PyPDF2 import PdfReader
from app.parsers.base_parser import BaseParser, ParsedChunk


class PDFParser(BaseParser):

    @staticmethod
    def supported_extensions() -> List[str]:
        return [".pdf"]

    async def parse(self, file_path: str, filename: str) -> List[ParsedChunk]:
        chunks = self._extract_text(file_path, filename)
        if not chunks:
            chunks = self._extract_ocr(file_path, filename)
        return chunks

    # ── Text layer (PyPDF2) ──────────────────────────────────
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

    # ── OCR fallback (pymupdf + pytesseract) ─────────────────
    def _extract_ocr(self, file_path: str, filename: str) -> List[ParsedChunk]:
        try:
            import fitz  # pymupdf
            import pytesseract
            from PIL import Image
            import io

            doc = fitz.open(file_path)
            chunks = []
            total = len(doc)

            for page_num in range(total):
                page = doc[page_num]
                # Render at 2x resolution for better OCR accuracy
                mat = fitz.Matrix(3.0, 3.0)
                pix = page.get_pixmap(matrix=mat)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img, lang="chi_sim+eng")
                if text and text.strip():
                    chunks.append(ParsedChunk(
                        text=text.strip(),
                        metadata={"source": filename, "file_type": "pdf",
                                  "page_number": page_num + 1, "total_pages": total,
                                  "ocr": True},
                        page_number=page_num + 1,
                    ))
            doc.close()
            return chunks
        except Exception as e:
            return []
