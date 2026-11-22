import os

from app.core.config import Settings
from app.core.tracing import configure_tracing, redact_trace_metadata


def test_tracing_disabled_by_config() -> None:
    settings = Settings(
        langsmith_tracing=False,
        langsmith_api_key="some-key",
        database_url="sqlite:///:memory:",
    )
    result = configure_tracing(settings)
    assert result is False
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "false"


def test_tracing_enabled_without_api_key_does_not_fail() -> None:
    settings = Settings(
        langsmith_tracing=True,
        langsmith_api_key="",
        database_url="sqlite:///:memory:",
    )
    result = configure_tracing(settings)
    assert result is False
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "false"


def test_tracing_enabled_with_key_configures_env() -> None:
    settings = Settings(
        langsmith_tracing=True,
        langsmith_api_key="lsv2_pt_test_key_12345",
        langsmith_project="test-project",
        database_url="sqlite:///:memory:",
    )
    result = configure_tracing(settings)
    assert result is True
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_API_KEY") == "lsv2_pt_test_key_12345"
    assert os.environ.get("LANGCHAIN_PROJECT") == "test-project"


def test_trace_metadata_redaction() -> None:
    raw_metadata = {
        "user_query": "Which remote did team TS3006 design?",
        "api_key": "secret-12345",
        "db_password": "supersecretpassword",
        "transcript_raw": "Speaker A: Hello everyone...",
    }
    redacted = redact_trace_metadata(raw_metadata)
    assert redacted["user_query"] == "Which remote did team TS3006 design?"
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["db_password"] == "[REDACTED]"
    assert redacted["transcript_raw"] == "[REDACTED]"
