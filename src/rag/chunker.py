"""Sentence-aware text chunking."""

import hashlib
import re

from src.config.settings import Settings
from src.models.domain import DocumentChunk, RawDocument

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑÜ])")


class SentenceAwareChunker:
    """Splits documents into overlapping chunks respecting sentence boundaries."""

    def __init__(self, settings: Settings) -> None:
        self._chunk_size = settings.chunk_size
        self._overlap = settings.chunk_overlap

    def chunk_documents(self, documents: list[RawDocument]) -> list[DocumentChunk]:
        """Chunk all raw documents into DocumentChunk instances."""
        chunks: list[DocumentChunk] = []
        for doc in documents:
            doc_chunks = self._chunk_text(doc.text, doc.filename)
            chunks.extend(doc_chunks)
        return chunks

    def _chunk_text(self, text: str, source_file: str) -> list[DocumentChunk]:
        """Split a single document text into chunks."""
        sentences = _SENTENCE_SPLIT.split(text)
        if not sentences:
            sentences = [text]

        chunks: list[DocumentChunk] = []
        current_parts: list[str] = []
        current_len = 0
        chunk_index = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sent_len = len(sentence) + (1 if current_parts else 0)
            if current_len + sent_len > self._chunk_size and current_parts:
                chunk_text = " ".join(current_parts)
                chunks.append(
                    self._make_chunk(chunk_text, source_file, chunk_index)
                )
                chunk_index += 1
                current_parts = self._overlap_tail(current_parts)
                current_len = sum(len(p) for p in current_parts) + max(
                    0, len(current_parts) - 1
                )

            current_parts.append(sentence)
            current_len += sent_len

        if current_parts:
            chunk_text = " ".join(current_parts)
            if chunk_text.strip():
                chunks.append(
                    self._make_chunk(chunk_text, source_file, chunk_index)
                )

        return chunks

    def _overlap_tail(self, parts: list[str]) -> list[str]:
        """Keep trailing sentences that fit within the overlap window."""
        if self._overlap <= 0:
            return []

        tail: list[str] = []
        total = 0
        for part in reversed(parts):
            addition = len(part) + (1 if tail else 0)
            if total + addition > self._overlap:
                break
            tail.insert(0, part)
            total += addition
        return tail

    def _make_chunk(
        self, text: str, source_file: str, chunk_index: int
    ) -> DocumentChunk:
        """Create a DocumentChunk with a stable ID."""
        chunk_id = hashlib.sha256(
            f"{source_file}:{chunk_index}:{text[:50]}".encode()
        ).hexdigest()[:16]
        return DocumentChunk(
            chunk_id=chunk_id,
            text=text.strip(),
            source_file=source_file,
            chunk_index=chunk_index,
            metadata={},
        )
