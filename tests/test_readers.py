"""Tests for document readers."""

from pathlib import Path

import pytest

from src.ingest.readers import JsonReader, MdReader, PdfReaderDoc, TxtReader

DOCS_PATH = Path(__file__).resolve().parent.parent / "docs"


@pytest.fixture
def docs_path() -> Path:
    return DOCS_PATH


def test_txt_reader(docs_path: Path) -> None:
    files = list(docs_path.glob("*.txt"))
    assert files, "No .txt files in docs/"
    text = TxtReader().read(files[0])
    assert len(text) > 50
    assert "base de datos" in text.lower() or "material" in text.lower()


def test_md_reader(docs_path: Path) -> None:
    files = list(docs_path.glob("*.md"))
    assert files, "No .md files in docs/"
    text = MdReader().read(files[0])
    assert "ERR-AUTH" in text or "credenciales" in text.lower()


def test_json_reader_flattens(docs_path: Path) -> None:
    files = list(docs_path.glob("*.json"))
    assert files, "No .json files in docs/"
    text = JsonReader().read(files[0])
    assert "[ID:" in text
    assert "Causas posibles" in text or "causas" in text.lower()


def test_pdf_reader(docs_path: Path) -> None:
    files = list(docs_path.glob("*.pdf"))
    assert files, "No .pdf files in docs/"
    text = PdfReaderDoc().read(files[0])
    assert len(text) > 20
