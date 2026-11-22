import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(
        app_name="Custom App",
        database_url="sqlite:///:memory:",
    )
    assert settings.app_name == "Custom App"
    assert settings.backend_port == 8000
    assert "http://localhost:5173" in settings.allowed_origins


def test_cors_origins_parsing_from_string() -> None:
    settings = Settings(
        allowed_origins="http://localhost:3000, https://app.catalist.ai",
        database_url="sqlite:///:memory:",
    )
    assert settings.allowed_origins == ["http://localhost:3000", "https://app.catalist.ai"]


def test_invalid_port_raises_error() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            backend_port=70000,  # Invalid port > 65535
            database_url="sqlite:///:memory:",
        )
    assert "backend_port" in str(excinfo.value)


def test_invalid_environment_raises_error() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            app_env="invalid_environment",  # Not in Literal
            database_url="sqlite:///:memory:",
        )
    assert "app_env" in str(excinfo.value)
