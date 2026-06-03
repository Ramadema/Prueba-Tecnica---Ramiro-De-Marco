"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the RAG assistant."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    docs_path: Path = Path("./docs")
    faiss_index_path: Path = Path("./storage/faiss/index.faiss")
    metadata_path: Path = Path("./storage/metadata/chunks.json")

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 500
    chunk_overlap: int = 80
    top_k: int = 4
    min_score: float = 0.35

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_sec: int = 60

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    insufficient_context_message: str = (
        "No encontré información suficiente en la documentación proporcionada."
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
