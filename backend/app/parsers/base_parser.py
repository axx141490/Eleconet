"""Base parser interface for all document types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ParsedChunk:
    """Represents a parsed text chunk from a document."""
    text: str
    metadata: dict
    page_number: Optional[int] = None
    chunk_index: int = 0


class BaseParser(ABC):
    """Abstract base class for all document parsers."""

    @abstractmethod
    async def parse(self, file_path: str, filename: str) -> List[ParsedChunk]:
        """Parse a file and return a list of text chunks with metadata."""
        pass

    @staticmethod
    def supported_extensions() -> List[str]:
        """Return a list of supported file extensions."""
        return []
