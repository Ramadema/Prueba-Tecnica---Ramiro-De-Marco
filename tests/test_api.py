"""API endpoint tests."""

from unittest.mock import AsyncMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import set_app_state
from src.models.domain import DocumentChunk
from src.models.schemas import AskResponse


@pytest.fixture
def indexed_client(app_state) -> TestClient:
    """Client with a minimal in-memory index (no real embeddings model)."""
    from src.main import app

    state = app_state
    chunks = [
        DocumentChunk(
            chunk_id="c1",
            text="Error de conexión con la base de datos. Verificar servidor activo.",
            source_file="doc.txt",
            chunk_index=0,
        )
    ]
    embeddings = np.ones((1, 384), dtype=np.float32)
    embeddings = embeddings / np.linalg.norm(embeddings)
    state.vector_store.build(chunks, embeddings)
    set_app_state(state)

    with TestClient(app) as client:
        yield client


def test_health(indexed_client: TestClient) -> None:
    response = indexed_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["index_loaded"] is True
    assert data["chunk_count"] == 1


def test_ask_empty_question(indexed_client: TestClient) -> None:
    response = indexed_client.post("/ask", json={"question": "   "})
    assert response.status_code == 422 or response.status_code == 400


def test_ask_no_index(client: TestClient) -> None:
    response = client.post("/ask", json={"question": "test"})
    assert response.status_code == 503


def test_ask_with_mocked_ollama(indexed_client: TestClient) -> None:
    mock_response = AskResponse(
        answer="Revise la conexión con el servidor de base de datos.",
        sources=[],
    )
    with patch(
        "src.services.rag_service.RagService.ask",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = indexed_client.post(
            "/ask", json={"question": "error de base de datos"}
        )
    assert response.status_code == 200
    assert "base de datos" in response.json()["answer"].lower()


def test_reindex(indexed_client: TestClient) -> None:
    def fake_encode(texts: list[str]) -> np.ndarray:
        n = len(texts)
        emb = np.ones((n, 384), dtype=np.float32)
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        return emb / norms

    with patch(
        "src.rag.embedder.EmbeddingService.encode", side_effect=fake_encode
    ):
        response = indexed_client.post("/reindex")
    assert response.status_code == 200
    data = response.json()
    assert data["chunks"] > 0
    assert data["documents"] > 0
