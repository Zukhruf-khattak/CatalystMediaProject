import os
from typing import Dict

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger("app.tracing")


def configure_tracing(settings: Settings) -> bool:
    """
    Configures LangSmith / LangChain tracing safely through standard environment variables.
    If tracing is disabled or credentials are missing, startup continues normally without failure.

    Returns:
        bool: True if tracing was successfully activated, False otherwise.
    """
    if not settings.langsmith_tracing:
        logger.info("LangSmith tracing is disabled by configuration (LANGSMITH_TRACING=false).")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False

    if not settings.langsmith_api_key or not settings.langsmith_api_key.strip():
        logger.warning(
            "LangSmith tracing enabled but LANGSMITH_API_KEY is not provided. "
            "Tracing will remain disabled to prevent startup or runtime failures."
        )
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False

    # Configure supported environment variables for LangSmith / LangChain V2
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    logger.info(
        f"LangSmith tracing successfully enabled for project: '{settings.langsmith_project}' "
        f"at endpoint '{settings.langsmith_endpoint}'."
    )
    return True


def redact_trace_metadata(metadata: Dict[str, str]) -> Dict[str, str]:
    """
    Enforces trace privacy and redaction policy.
    Ensures secrets, raw transcript text, and authorization tokens are scrubbed.
    """
    redacted = {}
    sensitive_keys = {"api_key", "password", "token", "transcript_raw", "secret"}
    for k, v in metadata.items():
        if any(s in k.lower() for s in sensitive_keys):
            redacted[k] = "[REDACTED]"
        else:
            redacted[k] = v
    return redacted
