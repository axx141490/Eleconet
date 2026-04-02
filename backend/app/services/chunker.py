"""Text chunking service for splitting documents into manageable pieces."""

from typing import List
from dataclasses import dataclass
from app.core.config import get_settings

settings = get_settings()


@dataclass
class TextChunk:
    """A chunk of text with metadata."""
    text: str
    metadata: dict
    chunk_index: int


class TextChunker:
    """Split text into overlapping chunks for embedding."""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def split_text(self, text: str, metadata: dict = None) -> List[TextChunk]:
        """Split text into chunks with overlap."""
        if not text.strip():
            return []

        metadata = metadata or {}

        # Split by paragraphs first, then by sentences if needed
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) + 2 > self.chunk_size:
                if current_chunk:
                    chunks.append(TextChunk(
                        text=current_chunk.strip(),
                        metadata={**metadata, "chunk_index": chunk_index},
                        chunk_index=chunk_index,
                    ))
                    chunk_index += 1

                    # Keep overlap from end of previous chunk
                    if self.chunk_overlap > 0:
                        overlap_text = current_chunk[-self.chunk_overlap:]
                        current_chunk = overlap_text + "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    # Single paragraph larger than chunk size - split by sentences
                    sub_chunks = self._split_long_text(para, metadata, chunk_index)
                    chunks.extend(sub_chunks)
                    chunk_index += len(sub_chunks)
                    current_chunk = ""
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(TextChunk(
                text=current_chunk.strip(),
                metadata={**metadata, "chunk_index": chunk_index},
                chunk_index=chunk_index,
            ))

        return chunks

    def _split_long_text(self, text: str, metadata: dict, start_index: int) -> List[TextChunk]:
        """Split a long text that exceeds chunk size by sentences or characters."""
        # Try splitting by sentences
        import re
        sentences = re.split(r'(?<=[.!?。！？])\s+', text)

        chunks = []
        current = ""
        idx = start_index

        for sentence in sentences:
            if len(current) + len(sentence) + 1 > self.chunk_size:
                if current:
                    chunks.append(TextChunk(
                        text=current.strip(),
                        metadata={**metadata, "chunk_index": idx},
                        chunk_index=idx,
                    ))
                    idx += 1
                    current = sentence
                else:
                    # Single sentence larger than chunk size - hard split
                    for i in range(0, len(sentence), self.chunk_size - self.chunk_overlap):
                        chunk_text = sentence[i:i + self.chunk_size]
                        chunks.append(TextChunk(
                            text=chunk_text.strip(),
                            metadata={**metadata, "chunk_index": idx},
                            chunk_index=idx,
                        ))
                        idx += 1
                    current = ""
            else:
                current = f"{current} {sentence}" if current else sentence

        if current.strip():
            chunks.append(TextChunk(
                text=current.strip(),
                metadata={**metadata, "chunk_index": idx},
                chunk_index=idx,
            ))

        return chunks
