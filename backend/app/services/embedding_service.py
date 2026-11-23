import os
from typing import Any, List, Optional

# Enforce offline mode so HuggingFace does not pause waiting for network timeouts
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger("app.services.embedding")


class EmbeddingServiceError(AppException):
    """Raised when embedding generation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=500)


class EmbeddingService:
    """Singleton service for local, CPU-compatible dense text embeddings."""

    _instance: Optional["EmbeddingService"] = None
    _model: Any = None

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
        return cls._instance

    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_name = self.settings.embedding_model_name
        self.expected_dim = self.settings.embedding_dim
        self.device = self.settings.embedding_device
        self.batch_size = self.settings.embedding_batch_size

    def _load_model(self) -> None:
        """Lazy-load the sentence transformer model once per process."""
        if self._model is not None:
            return

        logger.info(
            f"Loading local embedding model: '{self.model_name}' on device '{self.device}'..."
        )
        try:
            from sentence_transformers import SentenceTransformer

            # Load model with explicit device to guarantee CPU compatibility
            self._model = SentenceTransformer(
                model_name_or_path=self.model_name,
                device=self.device,
            )
            dim = getattr(
                self._model,
                "get_embedding_dimension",
                getattr(self._model, "get_sentence_embedding_dimension", lambda: 384),
            )()
            logger.info(f"Embedding model loaded successfully. Dimension: {dim}")
        except Exception as e:
            logger.error(f"Failed to load embedding model '{self.model_name}': {e}")
            raise EmbeddingServiceError(f"Failed to load embedding model: {e}") from e

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate 384-dimensional dense embeddings for a list of input texts in batches.

        Empty or whitespace-only texts produce a zero vector of the expected dimension.
        """
        if not texts:
            return []

        self._load_model()

        # Identify non-empty texts to embed, map back to original indices
        non_empty_indices = [i for i, t in enumerate(texts) if t and t.strip()]
        non_empty_texts = [texts[i] for i in non_empty_indices]

        # Allocate zero vectors for all outputs
        zero_vector = [0.0] * self.expected_dim
        all_embeddings: List[List[float]] = [zero_vector.copy() for _ in range(len(texts))]

        if not non_empty_texts:
            return all_embeddings

        try:
            # Batch encode with normalization for cosine distance
            raw_vectors = self._model.encode(
                sentences=non_empty_texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )

            for original_idx, vector in zip(non_empty_indices, raw_vectors):
                vec_list = vector.tolist()
                if len(vec_list) != self.expected_dim:
                    raise EmbeddingServiceError(
                        f"Expected dimension {self.expected_dim}, got {len(vec_list)}"
                    )
                all_embeddings[original_idx] = vec_list

            return all_embeddings

        except Exception as e:
            logger.error(f"Batch embedding generation error: {e}")
            raise EmbeddingServiceError(f"Embedding generation failed: {e}") from e

    def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text utterance."""
        results = self.generate_embeddings([text])
        return results[0]


_embedding_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Return singleton EmbeddingService instance."""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance
