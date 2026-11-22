import uuid

from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.core.exceptions import AppException
from app.main import create_application


def test_request_id_generated_when_absent(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    generated_id = response.headers["X-Request-ID"]
    # Check that generated ID is valid UUID
    parsed_uuid = uuid.UUID(generated_id)
    assert str(parsed_uuid) == generated_id


def test_request_id_propagated_when_valid(client: TestClient) -> None:
    custom_id = "test-custom-request-id-12345"
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


def test_request_id_sanitized_when_malicious(client: TestClient) -> None:
    malicious_id = "invalid id with spaces; DROP TABLE students;"
    response = client.get("/api/v1/health", headers={"X-Request-ID": malicious_id})
    assert response.status_code == 200
    # Must replace malicious ID with a fresh UUID
    returned_id = response.headers["X-Request-ID"]
    assert returned_id != malicious_id
    assert uuid.UUID(returned_id)


def test_process_time_header_present(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert "X-Process-Time-Ms" in response.headers
    time_val = float(response.headers["X-Process-Time-Ms"])
    assert time_val >= 0.0


def test_centralized_app_exception_handling() -> None:
    app = create_application()
    test_router = APIRouter()

    @test_router.get("/test-error")
    def trigger_error():
        raise AppException(
            message="Item not found in catalog",
            status_code=404,
            error_code="NOT_FOUND",
            details={"item_id": 99},
        )

    app.include_router(test_router)

    with TestClient(app) as test_client:
        response = test_client.get("/test-error")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
        assert data["error"]["message"] == "Item not found in catalog"
        assert data["error"]["details"] == {"item_id": 99}
        assert "request_id" in data["error"]
