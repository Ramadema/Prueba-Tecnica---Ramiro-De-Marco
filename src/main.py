"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.dependencies import get_app_state
from src.api.exceptions import (
    DocumentsNotFoundError,
    EmbeddingError,
    EmptyQuestionError,
    IndexNotFoundError,
    OllamaError,
    RagError,
)
from src.api.routes import router
from src.config.logging_config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load persisted index on startup."""
    setup_logging()
    state = get_app_state()

    if state.vector_store.exists() and not state.vector_store.is_loaded:
        try:
            state.vector_store.load()
            logger.info("Loaded existing FAISS index on startup.")
        except Exception:
            logger.warning("Failed to load existing index; run /reindex.", exc_info=True)
    else:
        logger.warning("No FAISS index found. Run POST /reindex to build one.")

    yield


app = FastAPI(
    title="RAG Support Assistant",
    description="Local RAG assistant for internal documentation support.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(router)


@app.exception_handler(EmptyQuestionError)
async def empty_question_handler(request: Request, exc: EmptyQuestionError):
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(DocumentsNotFoundError)
async def documents_not_found_handler(
    request: Request, exc: DocumentsNotFoundError
):
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(IndexNotFoundError)
async def index_not_found_handler(request: Request, exc: IndexNotFoundError):
    return JSONResponse(status_code=503, content={"detail": exc.message})


@app.exception_handler(OllamaError)
async def ollama_error_handler(request: Request, exc: OllamaError):
    return JSONResponse(status_code=503, content={"detail": exc.message})


@app.exception_handler(EmbeddingError)
async def embedding_error_handler(request: Request, exc: EmbeddingError):
    return JSONResponse(status_code=500, content={"detail": exc.message})


@app.exception_handler(RagError)
async def rag_error_handler(request: Request, exc: RagError):
    return JSONResponse(status_code=500, content={"detail": exc.message})
