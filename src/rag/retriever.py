"""Semantic retrieval over the FAISS vector store."""

import logging

from src.config.settings import Settings
from src.models.domain import ScoredChunk
from src.rag.embedder import EmbeddingService
from src.rag.vector_store import FaissVectorStore

logger = logging.getLogger(__name__)


class SemanticRetriever:
    """Retrieves top-k relevant chunks for a user question."""

    def __init__(
        self,
        settings: Settings,
        embedder: EmbeddingService,
        vector_store: FaissVectorStore,
    ) -> None:
        self._settings = settings
        self._embedder = embedder
        self._store = vector_store

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        min_score: float | None = None,
    ) -> list[ScoredChunk]:
        """Embed the question and return filtered top-k chunks."""
        k = top_k if top_k is not None else self._settings.top_k
        threshold = min_score if min_score is not None else self._settings.min_score

        query_vector = self._embedder.encode_query(question)
        candidates = self._store.search(query_vector, top_k=k)

        filtered = [c for c in candidates if c.score >= threshold]
        logger.info(
            "Retrieved %d/%d chunks above min_score=%.2f",
            len(filtered),
            len(candidates),
            threshold,
        )
        return filtered
