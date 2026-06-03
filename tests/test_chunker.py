"""Tests for SentenceAwareChunker."""

from src.config.settings import Settings
from src.models.domain import RawDocument
from src.rag.chunker import SentenceAwareChunker


def test_chunker_respects_size() -> None:
    settings = Settings(chunk_size=100, chunk_overlap=20)
    chunker = SentenceAwareChunker(settings)
    text = ". ".join(f"Oración número {i} con contenido." for i in range(20))
    doc = RawDocument(filename="test.txt", text=text, doc_type="txt")
    chunks = chunker.chunk_documents([doc])
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.text) <= settings.chunk_size + 100


def test_chunker_preserves_source() -> None:
    settings = Settings(chunk_size=200, chunk_overlap=30)
    chunker = SentenceAwareChunker(settings)
    doc = RawDocument(
        filename="doc.md",
        text="Primera oración. Segunda oración. Tercera oración.",
        doc_type="md",
    )
    chunks = chunker.chunk_documents([doc])
    assert all(c.source_file == "doc.md" for c in chunks)
    assert chunks[0].chunk_index == 0
