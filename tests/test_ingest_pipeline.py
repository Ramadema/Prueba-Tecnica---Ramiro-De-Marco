"""Tests for IngestPipeline."""

from src.config.settings import Settings
from src.ingest.pipeline import IngestPipeline


def test_ingest_pipeline_loads_docs() -> None:
    settings = Settings(docs_path="docs")
    pipeline = IngestPipeline(settings)
    documents = pipeline.run()
    assert len(documents) >= 3
    extensions = {d.doc_type for d in documents}
    assert "txt" in extensions or "md" in extensions
