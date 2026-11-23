import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn


@pytest.fixture
def api_test_data(db_session: Session):
    team = Team(id=uuid.uuid4(), team_code="TS3006")
    db_session.add(team)
    db_session.flush()

    m = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="ts3006a",
        meeting_number=1,
        sequence_letter="a",
        source_filename="TS3006a.txt",
        source_sha256="sha99",
        raw_text="Meeting a text",
    )
    db_session.add(m)
    db_session.flush()

    spk = Speaker(
        id=uuid.uuid4(),
        meeting_id=m.id,
        speaker_label="Speaker A",
        speaker_letter="A",
        role="Project Manager",
    )
    db_session.add(spk)
    db_session.flush()

    turn = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m.id,
        speaker_id=spk.id,
        turn_index=0,
        start_time_str="00:00:10",
        start_time_seconds=10,
        raw_text="We have agreed on titanium material for the casing.",
        normalized_text="we have agreed on titanium material for the casing",
        speaker=spk,
    )
    db_session.add(turn)
    db_session.commit()

    return {"team": team, "meeting": m, "turn": turn}


def test_api_process_query(client: TestClient):
    response = client.post(
        "/api/v1/retrieval/process-query",
        json={"query": "Team TS3006 planned an LCD screen and speech recognition."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["extracted_team"] == "TS3006"
    assert "lcd" in data["extracted_topics"]
    assert "speech recognition" in data["extracted_topics"]


def test_api_hybrid_search(client: TestClient, api_test_data):
    response = client.post(
        "/api/v1/retrieval/search",
        json={
            "query": "Team TS3006 titanium casing",
            "method": "keyword",
            "limit": 5,
        },
    )
    assert response.status_code == 200
    pack = response.json()
    assert pack["query"] == "Team TS3006 titanium casing"
    assert pack["retrieval_method"] == "keyword"
    assert len(pack["transcript_segments"]) >= 1
    assert pack["transcript_segments"][0]["speaker_label"] == "Speaker A"
    assert "titanium" in pack["transcript_segments"][0]["raw_text"].lower()
