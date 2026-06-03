"""Ingestion pipeline: read, clean, and return raw documents."""

import logging
from pathlib import Path

from src.api.exceptions import DocumentsNotFoundError
from src.config.settings import Settings
from src.ingest.cleaner import TextCleaner
from src.ingest.readers import SUPPORTED_EXTENSIONS, get_reader
from src.models.domain import RawDocument

logger = logging.getLogger(__name__)


class IngestPipeline:
    """Orchestrates document reading and text cleaning."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cleaner = TextCleaner()

    def run(self) -> list[RawDocument]:
        """Load and clean all supported documents from the docs folder."""
        docs_path = self._settings.docs_path
        if not docs_path.exists():
            raise DocumentsNotFoundError(f"Docs folder not found: {docs_path}")

        files = sorted(
            p
            for p in docs_path.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not files:
            raise DocumentsNotFoundError(
                f"No supported documents found in {docs_path}. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        documents: list[RawDocument] = []
        for path in files:
            try:
                reader = get_reader(path)
                raw_text = reader.read(path)
                cleaned = self._cleaner.clean(raw_text)
                if not cleaned:
                    logger.warning("Skipping empty document: %s", path.name)
                    continue
                documents.append(
                    RawDocument(
                        filename=path.name,
                        text=cleaned,
                        doc_type=path.suffix.lower().lstrip("."),
                    )
                )
                logger.info("Ingested: %s (%d chars)", path.name, len(cleaned))
            except Exception:
                logger.exception("Failed to ingest %s", path)
                raise

        if not documents:
            raise DocumentsNotFoundError("All documents were empty after cleaning.")

        return documents
