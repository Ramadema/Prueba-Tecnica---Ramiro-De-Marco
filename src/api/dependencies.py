"""FastAPI dependency injection and application state."""

from dataclasses import dataclass

from src.config.settings import Settings, get_settings
from src.ingest.pipeline import IngestPipeline
from src.rag.chunker import SentenceAwareChunker
from src.rag.embedder import EmbeddingService
from src.rag.generator import OllamaGenerator
from src.rag.retriever import SemanticRetriever
from src.rag.vector_store import FaissVectorStore
from src.services.index_service import IndexService
from src.services.rag_service import RagService


@dataclass
class AppState:
    """Holds shared service instances for the application lifetime."""

    settings: Settings
    vector_store: FaissVectorStore
    embedder: EmbeddingService
    retriever: SemanticRetriever
    generator: OllamaGenerator
    index_service: IndexService
    rag_service: RagService


def build_app_state() -> AppState:
    """Construct all service dependencies."""
    settings = get_settings()
    vector_store = FaissVectorStore(
        settings.faiss_index_path,
        settings.metadata_path,
    )
    embedder = EmbeddingService(settings)
    retriever = SemanticRetriever(settings, embedder, vector_store)
    generator = OllamaGenerator(settings)
    ingest_pipeline = IngestPipeline(settings)
    chunker = SentenceAwareChunker(settings)
    index_service = IndexService(
        settings, ingest_pipeline, chunker, embedder, vector_store
    )
    rag_service = RagService(settings, retriever, generator, vector_store)
    return AppState(
        settings=settings,
        vector_store=vector_store,
        embedder=embedder,
        retriever=retriever,
        generator=generator,
        index_service=index_service,
        rag_service=rag_service,
    )


_app_state: AppState | None = None


def get_app_state() -> AppState:
    """Return the global application state."""
    global _app_state
    if _app_state is None:
        _app_state = build_app_state()
    return _app_state


def set_app_state(state: AppState) -> None:
    """Override application state (used in tests)."""
    global _app_state
    _app_state = state
