"""Document readers for supported file formats."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
import chardet
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".json"}


class BaseDocumentReader(ABC):
    """Abstract base class for document readers."""

    @abstractmethod
    def read(self, path: Path) -> str:
        """Read and return raw text content from a file."""
        ...


class TxtReader(BaseDocumentReader):
    """Reader for plain text files."""

    def read(self, path: Path) -> str:
        return _read_text_file(path)


class MdReader(BaseDocumentReader):
    """Reader for Markdown files."""

    def read(self, path: Path) -> str:
        return _read_text_file(path)


def _read_text_file(path: Path) -> str:
    """Read a text file with UTF-8 and chardet fallback."""
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        detected = chardet.detect(raw)
        encoding = detected.get("encoding") or "latin-1"
        return raw.decode(encoding, errors="replace")


class PdfReaderDoc(BaseDocumentReader):
    """Reader for PDF files using pypdf."""

    def read(self, path: Path) -> str:
        reader = PdfReader(str(path))
        pages: list[str] = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"--- page {i} ---\n{text}")
        return "\n\n".join(pages)


class JsonReader(BaseDocumentReader):
    """Reader for JSON files; flattens MineCatalog-style documents."""

    def read(self, path: Path) -> str:
        raw = _read_text_file(path)
        data = json.loads(raw)
        if isinstance(data, dict) and "contenido" in data and isinstance(
            data["contenido"], list
        ):
            return "\n\n".join(_flatten_minecatalog_item(item) for item in data["contenido"])
        return json.dumps(data, ensure_ascii=False, indent=2)


def _flatten_minecatalog_item(item: dict) -> str:
    """Convert a structured JSON error item into searchable plain text."""
    lines = [f"[ID: {item.get('id', 'N/A')}]"]
    if title := item.get("titulo"):
        lines.append(f"Título: {title}")
    if msg := item.get("mensaje_usuario"):
        lines.append(f"Mensaje: {msg}")
    if cat := item.get("categoria"):
        lines.append(f"Categoría: {cat}")
    if causes := item.get("causas_posibles"):
        lines.append("Causas posibles:")
        lines.extend(f"- {c}" for c in causes)
    if solution := item.get("solucion"):
        lines.append("Solución:")
        if isinstance(solution, list):
            lines.extend(f"- {s}" for s in solution)
        else:
            lines.append(str(solution))
    if keywords := item.get("palabras_clave"):
        lines.append(f"Palabras clave: {', '.join(keywords)}")
    if level := item.get("nivel_soporte"):
        lines.append(f"Nivel de soporte: {level}")
    return "\n".join(lines)


READER_REGISTRY: dict[str, BaseDocumentReader] = {
    ".txt": TxtReader(),
    ".md": MdReader(),
    ".pdf": PdfReaderDoc(),
    ".json": JsonReader(),
}


def get_reader(path: Path) -> BaseDocumentReader:
    """Return the appropriate reader for a file extension."""
    ext = path.suffix.lower()
    if ext not in READER_REGISTRY:
        raise ValueError(f"Unsupported file extension: {ext}")
    return READER_REGISTRY[ext]
