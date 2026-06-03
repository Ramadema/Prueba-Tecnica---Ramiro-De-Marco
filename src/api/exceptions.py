"""Domain exceptions and FastAPI exception handlers."""


class RagError(Exception):
    """Base exception for RAG domain errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EmptyQuestionError(RagError):
    """Raised when the user question is empty or whitespace only."""


class DocumentsNotFoundError(RagError):
    """Raised when no documents are found in the docs folder."""


class IndexNotFoundError(RagError):
    """Raised when the FAISS index has not been built yet."""


class OllamaError(RagError):
    """Raised when Ollama is unreachable or returns an error."""


class EmbeddingError(RagError):
    """Raised when embedding generation fails."""
