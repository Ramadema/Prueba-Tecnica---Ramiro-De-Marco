"""Embedding generation using Sentence Transformers."""

import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from src.api.exceptions import EmbeddingError
from src.config.settings import Settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Wraps SentenceTransformer for batch and query encoding."""

    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.embedding_model
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a list of texts into L2-normalized embeddings."""
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, 384)
        try:
            model = self._get_model()
            embeddings = model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embeddings.astype(np.float32)
        except Exception as exc:
            raise EmbeddingError(f"Failed to generate embeddings: {exc}") from exc

    def encode_query(self, question: str) -> np.ndarray:
        """Encode a single query string."""
        result = self.encode([question])
        return result[0]
