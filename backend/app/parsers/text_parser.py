"""Parser for plain text files (.txt, .md, .csv, .json, .log, etc.)."""

import chardet
from typing import List
from app.parsers.base_parser import BaseParser, ParsedChunk


class TextParser(BaseParser):
    """Parse plain text files with encoding detection."""

    @staticmethod
    def supported_extensions() -> List[str]:
        return [".txt", ".md", ".csv", ".json", ".log", ".xml", ".yaml", ".yml", ".ini", ".cfg", ".conf"]

    async def parse(self, file_path: str, filename: str) -> List[ParsedChunk]:
        # Detect encoding
        with open(file_path, "rb") as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            encoding = detected.get("encoding", "utf-8") or "utf-8"

        text = raw_data.decode(encoding, errors="replace")

        if not text.strip():
            return []

        return [ParsedChunk(
            text=text,
            metadata={
                "source": filename,
                "file_type": "text",
                "encoding": encoding,
            }
        )]
