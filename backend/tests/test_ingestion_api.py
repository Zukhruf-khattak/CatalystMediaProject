import uuid

from fastapi.testclient import TestClient


def test_get_dataset_stats_empty(client: TestClient) -> None:
    response = client.get("/api/v1/ingestion/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_teams" in data
    assert "total_meetings" in data
    assert "total_speakers" in data
    assert "total_turns" in data
    assert "embedded_turns" in data


def test_get_nonexistent_job_returns_404(client: TestClient) -> None:
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/ingestion/jobs/{random_id}")
    assert response.status_code == 404
    data = response.json()
    error_msg = data.get("error", {}).get("message") or data.get("detail", "")
    assert f"'{random_id}' not found" in error_msg


def test_list_ingestion_jobs_empty(client: TestClient) -> None:
    response = client.get("/api/v1/ingestion/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total_count" in data
    assert isinstance(data["jobs"], list)


def test_create_sync_ingestion_job(client: TestClient) -> None:
    payload = {
        "force_reingest": False,
        "skip_embeddings": True,
        "limit_files": 1,
    }
    response = client.post("/api/v1/ingestion/jobs?sync=true", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert "status" in data
    assert data["status"] in ["COMPLETED", "RUNNING", "PARTIAL"]
