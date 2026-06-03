"""Pydantic schemas for API request and response bodies."""

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Request body for POST /ask."""

    question: str = Field(..., min_length=1, description="User question")


class SourceItem(BaseModel):
    """A source chunk used to generate the answer."""

    source_file: str
    chunk_index: int
    score: float
    excerpt: str


class AskResponse(BaseModel):
    """Response body for POST /ask."""

    answer: str
    sources: list[SourceItem]


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str
    index_loaded: bool
    chunk_count: int
    ollama_reachable: bool


class ReindexResponse(BaseModel):
    """Response body for POST /reindex."""

    documents: int
    chunks: int
    duration_sec: float
    message: str
