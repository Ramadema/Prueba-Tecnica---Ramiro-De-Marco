"""Tests for FaissVectorStore."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.models.domain import DocumentChunk
from src.rag.vector_store import FaissVectorStore


@pytest.fixture
def store_paths(tmp_path: Path):
    return tmp_path / "index.faiss", tmp_path / "chunks.json"


def test_build_search_persist(store_paths) -> None:
    index_path, meta_path = store_paths
    store = FaissVectorStore(index_path, meta_path)
    chunks = [
        DocumentChunk("a1", "error de base de datos", "doc.txt", 0),
        DocumentChunk("a2", "credenciales incorrectas", "doc.md", 0),
    ]
    embeddings = np.random.randn(2, 384).astype(np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms

    store.build(chunks, embeddings)
    assert store.exists()
    assert store.count() == 2

    store2 = FaissVectorStore(index_path, meta_path)
    store2.load()
    results = store2.search(embeddings[0], top_k=1)
    assert len(results) == 1
    assert results[0].score > 0.9
