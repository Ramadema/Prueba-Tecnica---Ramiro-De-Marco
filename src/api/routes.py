"""FastAPI route definitions."""

from fastapi import APIRouter, Request

from src.api.dependencies import get_app_state
from src.api.exceptions import RagError
from src.models.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    ReindexResponse,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Return service health and dependency status."""
    state = get_app_state()
    ollama_ok = await state.generator.is_reachable()
    return HealthResponse(
        status="ok" if ollama_ok else "degraded",
        index_loaded=state.vector_store.is_loaded,
        chunk_count=state.vector_store.count(),
        ollama_reachable=ollama_ok,
    )


@router.post("/reindex", response_model=ReindexResponse)
async def reindex(request: Request) -> ReindexResponse:
    """Reprocess all documents and rebuild the FAISS index."""
    state = get_app_state()
    return state.index_service.reindex()


@router.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest, request: Request) -> AskResponse:
    """Answer a user question using RAG."""
    state = get_app_state()
    return await state.rag_service.ask(body.question)
