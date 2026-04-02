"""Parser for image files using OCR (Tesseract) and OpenAI Vision."""

import base64
from typing import List
from app.parsers.base_parser import BaseParser, ParsedChunk
from app.core.config import get_settings

settings = get_settings()


class ImageParser(BaseParser):
    """Parse images using OCR and optionally OpenAI Vision API."""

    @staticmethod
    def supported_extensions() -> List[str]:
        return [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]

    async def parse(self, file_path: str, filename: str) -> List[ParsedChunk]:
        text_parts = []

        # Method 1: Try Tesseract OCR
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(file_path)
            ocr_text = pytesseract.image_to_string(img, lang="chi_sim+eng")
            if ocr_text.strip():
                text_parts.append(f"[OCR Text]\n{ocr_text.strip()}")
        except Exception:
            pass  # Tesseract may not be installed

        # Method 2: Use OpenAI Vision API for description
        if settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)

                with open(file_path, "rb") as img_file:
                    image_data = base64.b64encode(img_file.read()).decode("utf-8")

                # Determine MIME type
                ext = filename.rsplit(".", 1)[-1].lower()
                mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                            "gif": "image/gif", "bmp": "image/bmp", "webp": "image/webp"}
                mime_type = mime_map.get(ext, "image/png")

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Please describe this image in detail, including any text, charts, diagrams, or visual content. Respond in the same language as any text found in the image."},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                        ]
                    }],
                    max_tokens=1000,
                )
                description = response.choices[0].message.content
                if description:
                    text_parts.append(f"[Image Description]\n{description}")
            except Exception as e:
                text_parts.append(f"[Image description unavailable: {str(e)}]")

        if not text_parts:
            text_parts.append(f"[Image file: {filename} - no text could be extracted]")

        full_text = "\n\n".join(text_parts)
        return [ParsedChunk(
            text=full_text,
            metadata={
                "source": filename,
                "file_type": "image",
            }
        )]
