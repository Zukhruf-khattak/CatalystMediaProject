from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import create_application


def test_readiness_endpoint_healthy(client: TestClient) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] is True
    assert "app_name" in data
    assert data["environment"] == "testing"


def test_readiness_endpoint_database_failure() -> None:
    """When the database connection fails, /ready must return 503 with degraded status."""
    app = create_application()

    # Mock failing database session
    mock_failing_session = MagicMock()
    mock_failing_session.execute.side_effect = Exception("Connection timeout to PostgreSQL")

    def override_get_failing_db():
        yield mock_failing_session

    app.dependency_overrides[get_db] = override_get_failing_db

    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] is False

    app.dependency_overrides.clear()
