import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn


def seed_api_data(db: Session) -> None:
    team = Team(id=uuid.uuid4(), team_code="TS3006")
    meeting = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3006a",
        sequence_letter="a",
        meeting_number=1,
        source_filename="TS3006a.txt",
        source_sha256="sha_ts3006a",
        raw_text="The target selling price for the device is twenty-five Euros.",
    )
    speaker = Speaker(
        id=uuid.uuid4(),
        meeting_id=meeting.id,
        speaker_label="Speaker A",
        speaker_letter="A",
        role="Project Manager",
    )
    turn = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=meeting.id,
        speaker_id=speaker.id,
        turn_index=0,
        start_time_str="00:00:15",
        start_time_seconds=15,
        raw_text="The target selling price for the device is twenty-five Euros.",
        normalized_text="the target selling price for the device is twenty-five euros.",
    )
    db.add_all([team, meeting, speaker, turn])
    db.commit()


def test_api_agent_query_success(client: TestClient, db_session: Session) -> None:
    seed_api_data(db_session)
    payload = {
        "question": "What is the target selling price for Team TS3006?",
        "team_code": "TS3006",
    }
    response = client.post("/api/v1/agent/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == payload["question"]
    assert "answer" in data
    assert data["is_sufficient"] is True
    assert "session_id" in data
    assert len(data["steps_taken"]) >= 5


def test_api_agent_query_validation_error(client: TestClient) -> None:
    # Query too short (violates min_length=3)
    response = client.post("/api/v1/agent/query", json={"question": "a"})
    assert response.status_code == 422


def test_api_agent_session_aware_query(client: TestClient, db_session: Session) -> None:
    seed_api_data(db_session)
    session_id = str(uuid.uuid4())

    payload = {
        "question": "What is the target selling price?",
        "team_code": "TS3006",
    }
    response = client.post(f"/api/v1/agent/sessions/{session_id}/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id

    # Retrieve session history
    hist_response = client.get(f"/api/v1/agent/sessions/{session_id}")
    assert hist_response.status_code == 200
    hist_data = hist_response.json()
    assert hist_data["session_id"] == session_id
    assert hist_data["turn_count"] == 1


def test_api_agent_session_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/agent/sessions/non-existent-uuid")
    assert response.status_code == 404


def test_api_agent_status_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/agent/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "model_provider" in data
    assert "tools_available" in data
    assert len(data["tools_available"]) >= 4
