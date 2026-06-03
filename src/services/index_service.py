"""Index building and reindexing service."""

import logging
import time

from src.config.settings import Settings
from src.ingest.pipeline import IngestPipeline
from src.models.schemas import ReindexResponse
from src.rag.chunker import SentenceAwareChunker
from src.rag.embedder import EmbeddingService
from src.rag.vector_store import FaissVectorStore

logger = logging.getLogger(__name__)


class IndexService:
    """Orchestrates the full offline indexing pipeline."""

    def __init__(
        self,
        settings: Settings,
        ingest_pipeline: IngestPipeline,
        chunker: SentenceAwareChunker,
        embedder: EmbeddingService,
        vector_store: FaissVectorStore,
    ) -> None:
        self._settings = settings
        self._ingest = ingest_pipeline
        self._chunker = chunker
        self._embedder = embedder
        self._store = vector_store

    def reindex(self) -> ReindexResponse:
        """Run ingest → chunk → embed → index pipeline."""
        start = time.perf_counter()

        documents = self._ingest.run()
        chunks = self._chunker.chunk_documents(documents)
        texts = [c.text for c in chunks]
        embeddings = self._embedder.encode(texts)
        self._store.build(chunks, embeddings)

        duration = time.perf_counter() - start
        logger.info(
            "Reindex complete: %d docs, %d chunks in %.2fs",
            len(documents),
            len(chunks),
            duration,
        )
        return ReindexResponse(
            documents=len(documents),
            chunks=len(chunks),
            duration_sec=round(duration, 2),
            message="Index rebuilt successfully.",
        )
