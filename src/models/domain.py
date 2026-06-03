"""Domain models for the RAG pipeline."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RawDocument:
    """A document after ingestion and cleaning, before chunking."""

    filename: str
    text: str
    doc_type: str


@dataclass
class DocumentChunk:
    """A text chunk ready for embedding and indexing."""

    chunk_id: str
    text: str
    source_file: str
    chunk_index: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredChunk:
    """A chunk returned from semantic search with its relevance score."""

    chunk: DocumentChunk
    score: float
