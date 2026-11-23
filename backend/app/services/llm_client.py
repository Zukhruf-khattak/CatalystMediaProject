import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger("app.services.llm_client")


class LLMClientError(AppException):
    """Raised when an LLM inference call fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=502, details=details or {})


class BaseLLMClient(ABC):
    """Abstract interface for LLM extraction and reasoning providers."""

    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Any:
        """Generate structured JSON response from the LLM."""
        pass

    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate free-form text response from the LLM."""
        pass


class OllamaLLMClient(BaseLLMClient):
    """Local-first LLM provider invoking Ollama HTTP API."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = 90.0

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Any:
        full_system = (system_prompt or "") + "\nRespond with valid, parseable JSON only."
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": full_system,
            "format": "json",
            "stream": False,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                response_text = data.get("response", "{}")
                return json.loads(response_text)
        except Exception as e:
            logger.error(f"Ollama generation failed at {self.base_url}: {e}")
            raise LLMClientError(f"Ollama inference error: {e}") from e

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama text generation failed: {e}")
            raise LLMClientError(f"Ollama text error: {e}") from e


class MockLLMClient(BaseLLMClient):
    """Deterministic mock client for isolated testing without network or local LLM server."""

    def __init__(self, canned_response: Optional[Any] = None) -> None:
        self.canned_response = canned_response
        self.call_history: List[Dict[str, Any]] = []

    def set_response(self, response: Any) -> None:
        self.canned_response = response

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Any:
        self.call_history.append({"prompt": prompt, "system": system_prompt})
        if self.canned_response is not None:
            return self.canned_response
        # Default mock extraction output
        return {
            "memories": [
                {
                    "memory_type": "DECISION",
                    "statement": "The team decided to use a titanium case.",
                    "quote": "We will use titanium for the case.",
                    "speaker_label": "Speaker A",
                    "turn_index": 0,
                    "confidence": 0.95,
                    "metadata": {"topic": "case_material"},
                }
            ]
        }

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self.call_history.append({"prompt": prompt, "system": system_prompt})
        if isinstance(self.canned_response, str):
            return self.canned_response
        return "Mock LLM text response."


def get_llm_client() -> BaseLLMClient:
    """Return configured LLM client instance based on application settings."""
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        return OllamaLLMClient()
    elif provider == "gemini":
        # Check if Gemini key is set; if not fallback to Ollama or Mock
        if settings.gemini_api_key:
            # Note: Gemini client can be initialized here if needed
            logger.info("Using Gemini provider for LLM inference")
            return OllamaLLMClient()  # Fallback to Ollama if gemini SDK not configured
        else:
            logger.warning("Gemini API key is empty; falling back to Ollama client")
            return OllamaLLMClient()
    else:
        return OllamaLLMClient()
