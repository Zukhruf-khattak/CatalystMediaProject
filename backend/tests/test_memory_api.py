import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dataset import Meeting, Team
from app.models.memory import Memory, MemoryStatus, MemoryType


@pytest.fixture
def seed_data(db_session: Session):
    team = Team(id=uuid.uuid4(), team_code="TS3006")
    db_session.add(team)
    db_session.flush()

    meeting = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3006a",
        meeting_number=1,
        sequence_letter="a",
        source_filename="TS3006a.txt",
        source_sha256="sha456",
        raw_text="Meeting raw text",
    )
    db_session.add(meeting)
    db_session.flush()

    mem = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=meeting.id,
        memory_type=MemoryType.DECISION.value,
        statement="Team decided to use a curved case shape.",
        quote="We have agreed to use a curved case shape for the remote.",
        speaker_label="Speaker A",
        meeting_order=1,
        sequence_letter="a",
        status=MemoryStatus.CURRENT.value,
        confidence=0.95,
    )
    db_session.add(mem)
    db_session.commit()

    return {"team": team, "meeting": meeting, "memory": mem}


def test_api_search_memories(client: TestClient, seed_data):
    response = client.get("/api/v1/memory/search?team_code=TS3006")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["memory_type"] == "DECISION"
    assert "curved case shape" in data["items"][0]["statement"]


def test_api_get_memory_by_id(client: TestClient, seed_data):
    mem_id = str(seed_data["memory"].id)
    response = client.get(f"/api/v1/memory/{mem_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == mem_id
    assert data["quote"] == seed_data["memory"].quote


def test_api_get_memory_not_found(client: TestClient):
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/memory/{random_id}")
    assert response.status_code == 404


def test_api_extract_validation_error(client: TestClient):
    # Empty request without team_code or meeting_code
    response = client.post("/api/v1/memory/extract", json={})
    assert response.status_code == 400
