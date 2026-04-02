"""Factory for selecting the appropriate parser based on file type."""

import os
from typing import List, Optional
from app.parsers.base_parser import BaseParser, ParsedChunk
from app.parsers.text_parser import TextParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.docx_parser import DocxParser
from app.parsers.xlsx_parser import XlsxParser
from app.parsers.pptx_parser import PptxParser
from app.parsers.image_parser import ImageParser
from app.parsers.audio_video_parser import AudioParser, VideoParser
from app.models.knowledge_base import FileType


class ParserFactory:
    """Factory to create the right parser for a given file type."""

    _parsers: List[BaseParser] = [
        TextParser(),
        PDFParser(),
        DocxParser(),
        XlsxParser(),
        PptxParser(),
        ImageParser(),
        AudioParser(),
        VideoParser(),
    ]

    _extension_map: dict = {}

    @classmethod
    def _build_extension_map(cls):
        if not cls._extension_map:
            for parser in cls._parsers:
                for ext in parser.supported_extensions():
                    cls._extension_map[ext.lower()] = parser

    @classmethod
    def get_parser(cls, filename: str) -> Optional[BaseParser]:
        """Get the appropriate parser for a given filename."""
        cls._build_extension_map()
        ext = os.path.splitext(filename)[1].lower()
        return cls._extension_map.get(ext)

    @classmethod
    def detect_file_type(cls, filename: str) -> FileType:
        """Detect the file type category from filename."""
        ext = os.path.splitext(filename)[1].lower()
        type_map = {
            ".txt": FileType.TEXT, ".md": FileType.TEXT, ".csv": FileType.TEXT,
            ".json": FileType.TEXT, ".log": FileType.TEXT, ".xml": FileType.TEXT,
            ".yaml": FileType.TEXT, ".yml": FileType.TEXT,
            ".pdf": FileType.PDF,
            ".docx": FileType.DOCX, ".doc": FileType.DOCX,
            ".xlsx": FileType.XLSX, ".xls": FileType.XLSX,
            ".pptx": FileType.PPTX, ".ppt": FileType.PPTX,
            ".png": FileType.IMAGE, ".jpg": FileType.IMAGE, ".jpeg": FileType.IMAGE,
            ".gif": FileType.IMAGE, ".bmp": FileType.IMAGE, ".webp": FileType.IMAGE,
            ".mp3": FileType.AUDIO, ".wav": FileType.AUDIO, ".m4a": FileType.AUDIO,
            ".ogg": FileType.AUDIO, ".flac": FileType.AUDIO,
            ".mp4": FileType.VIDEO, ".avi": FileType.VIDEO, ".mkv": FileType.VIDEO,
            ".mov": FileType.VIDEO, ".wmv": FileType.VIDEO, ".webm": FileType.VIDEO,
        }
        return type_map.get(ext, FileType.UNKNOWN)

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get all supported file extensions."""
        cls._build_extension_map()
        return list(cls._extension_map.keys())

    @classmethod
    async def parse_file(cls, file_path: str, filename: str) -> List[ParsedChunk]:
        """Parse a file and return chunks."""
        parser = cls.get_parser(filename)
        if parser is None:
            raise ValueError(f"Unsupported file type: {filename}")
        return await parser.parse(file_path, filename)
