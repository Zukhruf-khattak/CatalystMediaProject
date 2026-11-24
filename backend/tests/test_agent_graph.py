import uuid

import pytest
from sqlalchemy.orm import Session

from app.agent.graph import build_agent_graph
from app.agent.nodes import AgentNodes
from app.agent.tools import AgentTools
from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn
from app.services.llm_client import MockLLMClient


@pytest.fixture
def graph_test_db(db_session: Session) -> Session:
    """Seed test data for graph execution and isolation tests."""
    # Team TS3006
    team1 = Team(id=uuid.uuid4(), team_code="TS3006")
    m1a = Meeting(
        id=uuid.uuid4(),
        team_id=team1.id,
        meeting_code="TS3006a",
        sequence_letter="a",
        meeting_number=1,
        source_filename="TS3006a.txt",
        source_sha256="sha_ts3006a",
        raw_text="Meeting TS3006a transcript text",
    )
    m1b = Meeting(
        id=uuid.uuid4(),
        team_id=team1.id,
        meeting_code="TS3006b",
        sequence_letter="b",
        meeting_number=2,
        source_filename="TS3006b.txt",
        source_sha256="sha_ts3006b",
        raw_text="Meeting TS3006b transcript text",
    )
    spk1a = Speaker(
        id=uuid.uuid4(),
        meeting_id=m1a.id,
        speaker_label="Speaker A",
        speaker_letter="A",
        role="Project Manager",
    )
    spk1b = Speaker(
        id=uuid.uuid4(),
        meeting_id=m1b.id,
        speaker_label="Speaker B",
        speaker_letter="B",
        role="Industrial Designer",
    )
    turn1a = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m1a.id,
        speaker_id=spk1a.id,
        turn_index=0,
        start_time_str="00:00:10",
        start_time_seconds=10,
        raw_text="We initially decided to use titanium for the remote casing.",
        normalized_text="we initially decided to use titanium for the remote casing",
    )
    turn1b = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m1b.id,
        speaker_id=spk1b.id,
        turn_index=1,
        start_time_str="00:00:20",
        start_time_seconds=20,
        raw_text="Titanium is far too heavy and expensive so we switched to curved plastic.",
        normalized_text="titanium is far too heavy and expensive so we switched to curved plastic",
    )

    # Team ES2003 (isolation test)
    team2 = Team(id=uuid.uuid4(), team_code="ES2003")
    m2a = Meeting(
        id=uuid.uuid4(),
        team_id=team2.id,
        meeting_code="ES2003a",
        sequence_letter="a",
        meeting_number=1,
        source_filename="ES2003a.txt",
        source_sha256="sha_es2003a",
        raw_text="Meeting ES2003a transcript text",
    )
    spk2a = Speaker(
        id=uuid.uuid4(),
        meeting_id=m2a.id,
        speaker_label="Speaker C",
        speaker_letter="C",
        role="UI Designer",
    )
    turn2a = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m2a.id,
        speaker_id=spk2a.id,
        turn_index=0,
        start_time_str="00:00:05",
        start_time_seconds=5,
        raw_text="Team ES2003 opted for a double curved rubber case.",
        normalized_text="team es2003 opted for a double curved rubber case",
    )

    db_session.add_all([team1, m1a, m1b, spk1a, spk1b, turn1a, turn1b, team2, m2a, spk2a, turn2a])
    db_session.commit()
    return db_session


def test_agent_graph_execution_success(graph_test_db: Session) -> None:
    """Verify end-to-end execution through all 8 nodes of the LangGraph workflow."""
    tools = AgentTools(graph_test_db)
    mock_llm = MockLLMClient(
        canned_response="Team TS3006 initially planned on titanium in TS3006a, but Speaker B in TS3006b switched to curved plastic due to weight and cost."
    )
    nodes = AgentNodes(tools=tools, llm_client=mock_llm)
    graph = build_agent_graph(nodes)

    initial_state = {
        "question": "What casing material did Team TS3006 initially plan and why did they switch in TS3006b?",
        "team_code": "TS3006",
        "iteration": 0,
        "max_iterations": 2,
    }

    result = graph.invoke(initial_state)

    assert result["is_sufficient"] is True
    assert "curved plastic" in result["answer"]
    assert "titanium" in result["answer"].lower()
    assert len(result["citations"]) >= 1
    assert "input_validation" in result["steps_taken"]
    assert "query_analysis" in result["steps_taken"]
    assert "retrieval_planning" in result["steps_taken"]
    assert "tool_execution" in result["steps_taken"]
    assert "evidence_assessment" in result["steps_taken"]
    assert "answer_generation" in result["steps_taken"]
    assert "response_validation" in result["steps_taken"]
    assert "final_response" in result["steps_taken"]


def test_agent_graph_input_validation_failure(graph_test_db: Session) -> None:
    """Verify that an invalid or empty query shortcuts to final_response."""
    tools = AgentTools(graph_test_db)
    nodes = AgentNodes(tools=tools)
    graph = build_agent_graph(nodes)

    result = graph.invoke({"question": "  ", "iteration": 0, "max_iterations": 2})

    assert result["is_sufficient"] is False
    assert "error" in result
    assert result["steps_taken"] == ["input_validation", "final_response"]


def test_agent_graph_insufficient_evidence_handling(graph_test_db: Session) -> None:
    """Verify that a query with zero matching evidence halts with is_sufficient=False."""
    tools = AgentTools(graph_test_db)
    nodes = AgentNodes(tools=tools)
    graph = build_agent_graph(nodes)

    result = graph.invoke(
        {
            "question": "Did the team decide to use solar powered nuclear fusion cells for the remote?",
            "team_code": "TS3006",
            "iteration": 0,
            "max_iterations": 2,
        }
    )

    assert result["is_sufficient"] is False
    assert result["insufficient_reason"] is not None
    assert "final_response" in result["steps_taken"]


def test_agent_graph_team_isolation(graph_test_db: Session) -> None:
    """Verify that evidence from team ES2003 is strictly isolated from team TS3006 queries."""
    tools = AgentTools(graph_test_db)
    nodes = AgentNodes(tools=tools)
    graph = build_agent_graph(nodes)

    result = graph.invoke(
        {
            "question": "What case did the team choose?",
            "team_code": "TS3006",
            "iteration": 0,
            "max_iterations": 2,
        }
    )

    # Verify no ES2003 turns leaked into TS3006 retrieval
    for turn in result.get("retrieved_turns", []):
        assert "ES2003" not in (turn.get("meeting_id") or "")
        assert "double curved rubber" not in turn.get("text", "")


def test_agent_graph_model_empty_fallback(graph_test_db: Session) -> None:
    """Verify that an empty model response triggers deterministic fallback generation."""
    tools = AgentTools(graph_test_db)
    mock_llm = MockLLMClient(canned_response="")  # returns empty string
    nodes = AgentNodes(tools=tools, llm_client=mock_llm)
    graph = build_agent_graph(nodes)

    result = graph.invoke(
        {
            "question": "What happened regarding titanium casing in TS3006?",
            "team_code": "TS3006",
            "iteration": 0,
            "max_iterations": 2,
        }
    )

    assert result["is_sufficient"] is True
    assert result["answer"] is not None
    assert len(result["answer"]) > 10
    assert "TS3006" in result["answer"]
