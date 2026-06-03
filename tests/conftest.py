"""Pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import AppState, build_app_state, set_app_state
from src.config.settings import Settings, get_settings
from src.main import app


@pytest.fixture
def test_settings(tmp_path) -> Settings:
    """Settings isolated to a temporary directory (no persisted index)."""
    get_settings.cache_clear()
    return Settings(
        docs_path=tmp_path / "docs",
        faiss_index_path=tmp_path / "faiss" / "index.faiss",
        metadata_path=tmp_path / "metadata" / "chunks.json",
    )


@pytest.fixture
def app_state(test_settings: Settings) -> AppState:
    """Build application state with isolated storage paths."""
    (test_settings.docs_path).mkdir(parents=True, exist_ok=True)
    import shutil
    from pathlib import Path

    source_docs = Path("docs")
    if source_docs.exists():
        for f in source_docs.iterdir():
            if f.is_file():
                shutil.copy(f, test_settings.docs_path / f.name)

    from src.ingest.pipeline import IngestPipeline
    from src.rag.chunker import SentenceAwareChunker
    from src.rag.embedder import EmbeddingService
    from src.rag.generator import OllamaGenerator
    from src.rag.retriever import SemanticRetriever
    from src.rag.vector_store import FaissVectorStore
    from src.services.index_service import IndexService
    from src.services.rag_service import RagService

    vector_store = FaissVectorStore(
        test_settings.faiss_index_path,
        test_settings.metadata_path,
    )
    embedder = EmbeddingService(test_settings)
    retriever = SemanticRetriever(test_settings, embedder, vector_store)
    generator = OllamaGenerator(test_settings)
    ingest_pipeline = IngestPipeline(test_settings)
    chunker = SentenceAwareChunker(test_settings)
    index_service = IndexService(
        test_settings, ingest_pipeline, chunker, embedder, vector_store
    )
    rag_service = RagService(test_settings, retriever, generator, vector_store)
    return AppState(
        settings=test_settings,
        vector_store=vector_store,
        embedder=embedder,
        retriever=retriever,
        generator=generator,
        index_service=index_service,
        rag_service=rag_service,
    )


@pytest.fixture
def client(app_state: AppState) -> TestClient:
    """FastAPI test client with injected state (no disk index load)."""
    set_app_state(app_state)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
