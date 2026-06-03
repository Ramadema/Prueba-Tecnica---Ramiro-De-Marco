"""FAISS vector store with JSON metadata persistence."""

import json
import logging
from pathlib import Path

import faiss
import numpy as np

from src.models.domain import DocumentChunk, ScoredChunk

logger = logging.getLogger(__name__)


class FaissVectorStore:
    """Local FAISS index with parallel metadata storage."""

    def __init__(self, index_path: Path, metadata_path: Path) -> None:
        self._index_path = index_path
        self._metadata_path = metadata_path
        self._index: faiss.IndexFlatIP | None = None
        self._chunks: list[DocumentChunk] = []

    @property
    def is_loaded(self) -> bool:
        """Return True if an index is loaded in memory."""
        return self._index is not None and len(self._chunks) > 0

    def count(self) -> int:
        """Return number of indexed chunks."""
        return len(self._chunks)

    def exists(self) -> bool:
        """Return True if persisted index and metadata exist on disk."""
        return self._index_path.exists() and self._metadata_path.exists()

    def build(self, chunks: list[DocumentChunk], embeddings: np.ndarray) -> None:
        """Build and persist a new FAISS index from chunks and embeddings."""
        if len(chunks) == 0:
            raise ValueError("Cannot build index with zero chunks.")
        if embeddings.shape[0] != len(chunks):
            raise ValueError("Embeddings count must match chunks count.")

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings.astype(np.float32))

        self._index = index
        self._chunks = chunks
        self._persist()
        logger.info("Built FAISS index with %d chunks (dim=%d)", len(chunks), dim)

    def load(self) -> None:
        """Load index and metadata from disk."""
        if not self.exists():
            raise FileNotFoundError(
                f"Index not found at {self._index_path}. Run /reindex first."
            )
        self._index = faiss.read_index(str(self._index_path))
        with self._metadata_path.open(encoding="utf-8") as f:
            raw = json.load(f)
        self._chunks = [
            DocumentChunk(
                chunk_id=c["chunk_id"],
                text=c["text"],
                source_file=c["source_file"],
                chunk_index=c["chunk_index"],
                metadata=c.get("metadata", {}),
            )
            for c in raw
        ]
        logger.info("Loaded FAISS index with %d chunks", len(self._chunks))

    def search(self, query_vector: np.ndarray, top_k: int) -> list[ScoredChunk]:
        """Search for the top_k most similar chunks."""
        if self._index is None or not self._chunks:
            return []

        query = query_vector.reshape(1, -1).astype(np.float32)
        scores, indices = self._index.search(query, min(top_k, len(self._chunks)))

        results: list[ScoredChunk] = []
        for score, idx in zip(scores[0], indices[0], strict=True):
            if idx < 0:
                continue
            results.append(
                ScoredChunk(chunk=self._chunks[idx], score=float(score))
            )
        return results

    def _persist(self) -> None:
        """Write index and metadata to disk."""
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        self._metadata_path.parent.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self._index, str(self._index_path))
        metadata = [
            {
                "chunk_id": c.chunk_id,
                "text": c.text,
                "source_file": c.source_file,
                "chunk_index": c.chunk_index,
                "metadata": c.metadata,
            }
            for c in self._chunks
        ]
        with self._metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
