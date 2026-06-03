"""RAG orchestration: retrieve context and generate answer."""

import logging

from src.api.exceptions import EmptyQuestionError, IndexNotFoundError
from src.config.settings import Settings
from src.models.schemas import AskResponse, SourceItem
from src.rag.generator import OllamaGenerator
from src.rag.prompts import INSUFFICIENT_CONTEXT_MESSAGE, build_rag_prompt
from src.rag.retriever import SemanticRetriever
from src.rag.vector_store import FaissVectorStore

logger = logging.getLogger(__name__)

EXCERPT_MAX_LEN = 200


class RagService:
    """Coordinates retrieval and generation for user questions."""

    def __init__(
        self,
        settings: Settings,
        retriever: SemanticRetriever,
        generator: OllamaGenerator,
        vector_store: FaissVectorStore,
    ) -> None:
        self._settings = settings
        self._retriever = retriever
        self._generator = generator
        self._store = vector_store

    async def ask(self, question: str) -> AskResponse:
        """Answer a user question using RAG."""
        if not question or not question.strip():
            raise EmptyQuestionError("Question cannot be empty.")

        question = question.strip()

        if not self._store.is_loaded:
            raise IndexNotFoundError(
                "Vector index not loaded. Call POST /reindex first."
            )

        scored_chunks = self._retriever.retrieve(question)
        if not scored_chunks:
            return AskResponse(
                answer=self._settings.insufficient_context_message,
                sources=[],
            )

        sources = [
            SourceItem(
                source_file=sc.chunk.source_file,
                chunk_index=sc.chunk.chunk_index,
                score=round(sc.score, 4),
                excerpt=sc.chunk.text[:EXCERPT_MAX_LEN]
                + ("..." if len(sc.chunk.text) > EXCERPT_MAX_LEN else ""),
            )
            for sc in scored_chunks
        ]

        context_blocks = [sc.chunk.text for sc in scored_chunks]
        prompt = build_rag_prompt(question, context_blocks)
        answer = await self._generator.generate(prompt)

        if not answer:
            answer = self._settings.insufficient_context_message

        return AskResponse(answer=answer, sources=sources)
