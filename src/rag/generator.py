"""Ollama LLM generation client."""

import logging

import httpx

from src.api.exceptions import OllamaError
from src.config.settings import Settings

logger = logging.getLogger(__name__)


class OllamaGenerator:
    """Generates answers using a local Ollama model."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model
        self._timeout = settings.ollama_timeout_sec

    async def is_reachable(self) -> bool:
        """Check if Ollama API is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def generate(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the generated text."""
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                answer = data.get("response", "").strip()
                if not answer:
                    raise OllamaError("Ollama returned an empty response.")
                return answer
        except httpx.TimeoutException as exc:
            raise OllamaError(
                f"Ollama request timed out after {self._timeout}s."
            ) from exc
        except httpx.ConnectError as exc:
            raise OllamaError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Ensure Ollama is running."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaError(
                f"Ollama HTTP error {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except OllamaError:
            raise
        except Exception as exc:
            raise OllamaError(f"Ollama generation failed: {exc}") from exc
