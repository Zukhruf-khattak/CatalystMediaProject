from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["health_url"] == "/api/v1/health"
    assert data["readiness_url"] == "/api/v1/ready"


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert data["environment"] == "testing"

    # Confirm no credentials or database URLs leaked
    raw_text = response.text.lower()
    assert "password" not in raw_text
    assert "postgres" not in raw_text
    assert "secret" not in raw_text

