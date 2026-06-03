"""Prompt templates for grounded generation."""

INSUFFICIENT_CONTEXT_MESSAGE = (
    "No encontré información suficiente en la documentación proporcionada."
)

SYSTEM_INSTRUCTIONS = """Eres un asistente de soporte técnico especializado en documentación interna.
Reglas estrictas:
1. Responde ÚNICAMENTE usando la información del CONTEXTO proporcionado.
2. NUNCA inventes información, códigos de error, pasos o causas que no estén en el contexto.
3. Si el contexto no contiene información suficiente para responder, responde EXACTAMENTE:
"No encontré información suficiente en la documentación proporcionada."
4. Si hay un código de error en el contexto, menciónalo en tu respuesta.
5. Responde de forma clara, profesional y en español."""


def build_rag_prompt(question: str, context_blocks: list[str]) -> str:
    """Build the full prompt sent to Ollama."""
    numbered_context = "\n\n".join(
        f"[{i + 1}] {block}" for i, block in enumerate(context_blocks)
    )
    return f"""{SYSTEM_INSTRUCTIONS}

CONTEXTO:
{numbered_context}

PREGUNTA:
{question}

RESPUESTA:"""
