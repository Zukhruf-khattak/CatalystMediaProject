"""Comprehensive test suite for Phase 6: Deterministic Citation and Evidence Validation."""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.agent.graph import build_agent_graph
from app.agent.nodes import AgentNodes
from app.agent.tools import AgentTools
from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn
from app.services.citation_validation_service import CitationValidationService
from app.services.llm_client import MockLLMClient


@pytest.fixture
def validation_db(db_session: Session) -> Session:
    """Seed structured database fixtures across multiple teams and meetings."""
    # Team TS3006
    team_ts06 = Team(id=uuid.uuid4(), team_code="TS3006")
    m_ts06a = Meeting(
        id=uuid.uuid4(),
        team_id=team_ts06.id,
        meeting_code="TS3006a",
        sequence_letter="a",
        meeting_number=1,
        source_filename="TS3006a.txt",
        source_sha256="sha_ts06a",
        raw_text="Meeting TS3006a text",
    )
    m_ts06b = Meeting(
        id=uuid.uuid4(),
        team_id=team_ts06.id,
        meeting_code="TS3006b",
        sequence_letter="b",
        meeting_number=2,
        source_filename="TS3006b.txt",
        source_sha256="sha_ts06b",
        raw_text="Meeting TS3006b text",
    )

    spk_ts06_a = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_ts06a.id,
        speaker_label="Speaker A",
        speaker_letter="A",
        role="Project Manager",
    )
    spk_ts06_b = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_ts06b.id,
        speaker_label="Speaker B",
        speaker_letter="B",
        role="Industrial Designer",
    )

    turn_1 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_ts06a.id,
        speaker_id=spk_ts06_a.id,
        turn_index=0,
        start_time_str="00:01:00",
        start_time_seconds=60,
        raw_text="We initially decided to feature a double curved titanium case for the remote control.",
        normalized_text="we initially decided to feature a double curved titanium case for the remote control.",
    )
    turn_2 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_ts06a.id,
        speaker_id=spk_ts06_a.id,
        turn_index=1,
        start_time_str="00:01:30",
        start_time_seconds=90,
        raw_text="The budget constraints will strictly limit any exotic metals like titanium.",
        normalized_text="the budget constraints will strictly limit any exotic metals like titanium.",
    )
    turn_3 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_ts06b.id,
        speaker_id=spk_ts06_b.id,
        turn_index=0,
        start_time_str="00:05:00",
        start_time_seconds=300,
        raw_text="We must switch from titanium to curved plastic because titanium is too heavy.",
        normalized_text="we must switch from titanium to curved plastic because titanium is too heavy.",
    )

    # Team ES2003
    team_es03 = Team(id=uuid.uuid4(), team_code="ES2003")
    m_es03a = Meeting(
        id=uuid.uuid4(),
        team_id=team_es03.id,
        meeting_code="ES2003a",
        sequence_letter="a",
        meeting_number=1,
        source_filename="ES2003a.txt",
        source_sha256="sha_es03a",
        raw_text="Meeting ES2003a text",
    )
    spk_es03_c = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_es03a.id,
        speaker_label="Speaker C",
        speaker_letter="C",
        role="Marketing",
    )
    turn_4 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_es03a.id,
        speaker_id=spk_es03_c.id,
        turn_index=0,
        start_time_str="00:02:00",
        start_time_seconds=120,
        raw_text="Team ES2003 decided on a completely rubberized double curved enclosure.",
        normalized_text="team es2003 decided on a completely rubberized double curved enclosure.",
    )

    db_session.add_all(
        [
            team_ts06,
            m_ts06a,
            m_ts06b,
            spk_ts06_a,
            spk_ts06_b,
            turn_1,
            turn_2,
            turn_3,
            team_es03,
            m_es03a,
            spk_es03_c,
            turn_4,
        ]
    )
    db_session.commit()
    return db_session


# -----------------------------------------------------------------------------
# 1. Exact Quotation Matches
# -----------------------------------------------------------------------------
def test_exact_quotation_match(validation_db: Session) -> None:
    """Verify that a faithful verbatim quotation of >= 6 words passes individual validation."""
    service = CitationValidationService(validation_db)
    turn = validation_db.query(TranscriptTurn).filter(TranscriptTurn.turn_index == 0).first()

    citation = {
        "meeting_id": "TS3006a",
        "team_code": "TS3006",
        "turn_id": str(turn.id),
        "quote": "initially decided to feature a double curved titanium case",
        "speaker_label": "Speaker A",
        "speaker_role": "Project Manager",
    }
    result = service.validate_citation(citation, expected_team="TS3006")
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert result.word_count >= 6


# -----------------------------------------------------------------------------
# 2. Case and Spacing Normalization
# -----------------------------------------------------------------------------
def test_case_and_spacing_normalization(validation_db: Session) -> None:
    """Verify that uppercase casing and collapsed extra whitespace match verbatim text."""
    service = CitationValidationService(validation_db)
    turn = validation_db.query(TranscriptTurn).filter(TranscriptTurn.turn_index == 0).first()

    citation = {
        "meeting_id": "TS3006a",
        "team_code": "TS3006",
        "turn_id": str(turn.id),
        "quote": "INITIALLY   DECIDED TO   FEATURE a double curved   TITANIUM case",
        "speaker_label": "Speaker A",
    }
    result = service.validate_citation(citation, expected_team="TS3006")
    assert result.is_valid is True
    assert len(result.errors) == 0


# -----------------------------------------------------------------------------
# 3. Modified or Fabricated Quotations
# -----------------------------------------------------------------------------
def test_modified_or_fabricated_quotation(validation_db: Session) -> None:
    """Verify that paraphrased, fabricated, or altered quotes are deterministically rejected."""
    service = CitationValidationService(validation_db)
    turn = validation_db.query(TranscriptTurn).filter(TranscriptTurn.turn_index == 0).first()

    citation = {
        "meeting_id": "TS3006a",
        "team_code": "TS3006",
        "turn_id": str(turn.id),
        "quote": "We definitely decided to feature a polished golden casing for the device",
        "speaker_label": "Speaker A",
    }
    result = service.validate_citation(citation, expected_team="TS3006")
    assert result.is_valid is False
    assert any("not found verbatim" in err for err in result.errors)


# -----------------------------------------------------------------------------
# 4. Quotes Shorter than Six Words
# -----------------------------------------------------------------------------
def test_quote_shorter_than_six_words(validation_db: Session) -> None:
    """Verify that quotations containing fewer than 6 words violate Catalist constraints."""
    service = CitationValidationService(validation_db)
    turn = validation_db.query(TranscriptTurn).filter(TranscriptTurn.turn_index == 0).first()

    citation = {
        "meeting_id": "TS3006a",
        "team_code": "TS3006",
        "turn_id": str(turn.id),
        "quote": "We initially decided",  # only 3 words
        "speaker_label": "Speaker A",
    }
    result = service.validate_citation(citation, expected_team="TS3006")
    assert result.is_valid is False
    assert any("minimum required is 6" in err for err in result.errors)


# -----------------------------------------------------------------------------
# 5. Quotes Stitched Across Turns
# -----------------------------------------------------------------------------
def test_quote_stitched_across_turns(validation_db: Session) -> None:
    """Verify that combining text across separate turns into one quote is rejected."""
    service = CitationValidationService(validation_db)
    turn_1 = (
        validation_db.query(TranscriptTurn).filter(TranscriptTurn.start_time_seconds == 60).first()
    )

    # Stitched quote combining the tail of turn 1 and the head of turn 2
    stitched_quote = "double curved titanium case for the remote control The budget constraints will strictly limit"

    citation = {
        "meeting_id": "TS3006a",
        "team_code": "TS3006",
        "turn_id": str(turn_1.id),
        "quote": stitched_quote,
        "speaker_label": "Speaker A",
    }
    result = service.validate_citation(citation, expected_team="TS3006")
    assert result.is_valid is False
    assert any("not found verbatim" in err for err in result.errors)


# -----------------------------------------------------------------------------
# 6. Incorrect Meeting IDs
# -----------------------------------------------------------------------------
def test_incorrect_meeting_id(validation_db: Session) -> None:
    """Verify that citing a non-existent meeting code fails validation."""
    service = CitationValidationService(validation_db)

    citation = {
        "meeting_id": "TS9999z",
        "team_code": "TS3006",
        "quote": "initially decided to feature a double curved titanium case",
        "speaker_label": "Speaker A",
    }
    result = service.validate_citation(citation, expected_team="TS3006")
    assert result.is_valid is False
    assert any("does not exist in corpus" in err for err in result.errors)


# -----------------------------------------------------------------------------
# 7. Incorrect Team IDs
# -----------------------------------------------------------------------------
def test_incorrect_team_id(validation_db: Session) -> None:
    """Verify that citing a meeting from another team fails team consistency check."""
    service = CitationValidationService(validation_db)
    turn_4 = (
        validation_db.query(TranscriptTurn).filter(TranscriptTurn.start_time_seconds == 120).first()
    )

    citation = {
        "meeting_id": "ES2003a",
        "team_code": "TS3006",  # claimed TS3006, but meeting is ES2003
        "turn_id": str(turn_4.id),
        "quote": "Team ES2003 decided on a completely rubberized double curved enclosure.",
        "speaker_label": "Speaker C",
    }
    result = service.validate_citation(citation, expected_team="TS3006")
    assert result.is_valid is False
    assert any(
        "belongs to team 'ES2003', not expected team 'TS3006'" in err for err in result.errors
    )


# -----------------------------------------------------------------------------
# 8. Incorrect Speaker Labels
# -----------------------------------------------------------------------------
def test_incorrect_speaker_label(validation_db: Session) -> None:
    """Verify that attributing a quote to the wrong speaker letter is rejected."""
    service = CitationValidationService(validation_db)
    turn_1 = (
        validation_db.query(TranscriptTurn).filter(TranscriptTurn.start_time_seconds == 60).first()
    )

    citation = {
        "meeting_id": "TS3006a",
        "team_code": "TS3006",
        "turn_id": str(turn_1.id),
        "quote": "initially decided to feature a double curved titanium case",
        "speaker_label": "Speaker C",  # Actually spoken by Speaker A
    }
    result = service.validate_citation(citation, expected_team="TS3006")
    assert result.is_valid is False
    assert any("does not match turn speaker" in err for err in result.errors)


# -----------------------------------------------------------------------------
# 9. Duplicate Meeting Citations (Fails >= 2 Distinct Meetings Rule)
# -----------------------------------------------------------------------------
def test_duplicate_meeting_citations(validation_db: Session) -> None:
    """Verify that multiple valid citations from only one meeting fail the cross-meeting rule."""
    service = CitationValidationService(validation_db)
    turn_1 = (
        validation_db.query(TranscriptTurn).filter(TranscriptTurn.start_time_seconds == 60).first()
    )
    turn_2 = (
        validation_db.query(TranscriptTurn).filter(TranscriptTurn.start_time_seconds == 90).first()
    )

    answer = "Team TS3006 initially planned on titanium casing. However, budget constraints limited exotic metals."
    citations = [
        {
            "meeting_id": "TS3006a",
            "turn_id": str(turn_1.id),
            "quote": "initially decided to feature a double curved titanium case",
            "speaker_label": "Speaker A",
        },
        {
            "meeting_id": "TS3006a",
            "turn_id": str(turn_2.id),
            "quote": "budget constraints will strictly limit any exotic metals like titanium",
            "speaker_label": "Speaker A",
        },
    ]
    res = service.validate_answer(answer, citations, expected_team="TS3006")
    assert res.is_valid is False
    assert any("at least 2 meetings" in err for err in res.errors)


# -----------------------------------------------------------------------------
# 10. Evidence from Only One Meeting
# -----------------------------------------------------------------------------
def test_evidence_from_only_one_meeting(validation_db: Session) -> None:
    """Verify that an answer with only a single citation fails the cross-meeting requirement."""
    service = CitationValidationService(validation_db)
    turn_1 = (
        validation_db.query(TranscriptTurn).filter(TranscriptTurn.start_time_seconds == 60).first()
    )

    answer = "Team TS3006 initially planned on a titanium casing."
    citations = [
        {
            "meeting_id": "TS3006a",
            "turn_id": str(turn_1.id),
            "quote": "initially decided to feature a double curved titanium case",
            "speaker_label": "Speaker A",
        }
    ]
    res = service.validate_answer(answer, citations, expected_team="TS3006")
    assert res.is_valid is False
    assert any("cites 1 distinct meeting(s)" in err for err in res.errors)


# -----------------------------------------------------------------------------
# 11. Unsupported Answer Claims
# -----------------------------------------------------------------------------
def test_unsupported_answer_claims(validation_db: Session) -> None:
    """Verify that introducing facts with no lexical backing in citations triggers validation error."""
    service = CitationValidationService(validation_db)
    turn_1 = (
        validation_db.query(TranscriptTurn).filter(TranscriptTurn.start_time_seconds == 60).first()
    )
    turn_3 = (
        validation_db.query(TranscriptTurn).filter(TranscriptTurn.start_time_seconds == 300).first()
    )

    # Hallucinated answer claiming quantum computing and rocket propulsion
    hallucinated_answer = (
        "Team TS3006 manufactured quantum nuclear satellites with supersonic rocket propulsion. "
        "The project launched into planetary orbit."
    )
    citations = [
        {
            "meeting_id": "TS3006a",
            "turn_id": str(turn_1.id),
            "quote": "initially decided to feature a double curved titanium case",
            "speaker_label": "Speaker A",
        },
        {
            "meeting_id": "TS3006b",
            "turn_id": str(turn_3.id),
            "quote": "must switch from titanium to curved plastic because titanium is too heavy",
            "speaker_label": "Speaker B",
        },
    ]
    res = service.validate_answer(hallucinated_answer, citations, expected_team="TS3006")
    assert res.is_valid is False
    assert any("unsubstantiated claims" in err for err in res.errors)


# -----------------------------------------------------------------------------
# 12. Successful Validation and Retry Behavior
# -----------------------------------------------------------------------------
def test_successful_validation_and_retry_behavior(validation_db: Session) -> None:
    """Verify that LangGraph retries on validation failure and succeeds when evidence is corrected."""
    tools = AgentTools(validation_db)

    # First turn: returns invalid 4 sentences. Second turn: returns valid 2 sentences.
    turn_1_text = "Sentence one is here. Sentence two is here. Sentence three is here. Sentence four is too long."
    turn_2_text = (
        "Team TS3006 initially planned on a double curved titanium case in TS3006a. "
        "Speaker B switched to curved plastic in TS3006b."
    )
    responses = [turn_1_text, turn_2_text]

    mock_llm = MockLLMClient()
    mock_llm.generate_text = lambda *args, **kwargs: responses.pop(0) if responses else turn_2_text

    nodes = AgentNodes(tools=tools, llm_client=mock_llm)
    graph = build_agent_graph(nodes)

    initial_state = {
        "question": "What titanium casing did TS3006 switch from and to?",
        "team_code": "TS3006",
        "iteration": 0,
        "max_iterations": 2,
        "validation_retries": 0,
        "max_validation_retries": 2,
    }

    result = graph.invoke(initial_state)

    assert result["is_sufficient"] is True
    assert result["validation_status"] == "PASSED"
    assert len(result["validation_errors"]) == 0
    assert len(result["citations"]) >= 2
    assert len(result["supporting_meetings"]) >= 2
    assert "citation_validation" in result["steps_taken"]


# -----------------------------------------------------------------------------
# 13. Insufficient Evidence After Retries
# -----------------------------------------------------------------------------
def test_insufficient_evidence_after_retries(validation_db: Session) -> None:
    """Verify that exhausting validation retries halts with explicit failure response and empty citations."""
    tools = AgentTools(validation_db)

    # Mock LLM that always outputs 5 sentences to trigger continuous validation failure
    invalid_response = "Sentence 1. Sentence 2. Sentence 3. Sentence 4. Sentence 5 is invalid."
    mock_llm = MockLLMClient(canned_response=invalid_response)

    nodes = AgentNodes(tools=tools, llm_client=mock_llm)
    graph = build_agent_graph(nodes)

    initial_state = {
        "question": "What titanium casing did TS3006 switch from and to?",
        "team_code": "TS3006",
        "iteration": 0,
        "max_iterations": 2,
        "validation_retries": 0,
        "max_validation_retries": 2,
    }

    result = graph.invoke(initial_state)

    assert result["is_sufficient"] is False
    assert result["validation_status"] == "FAILED"
    assert len(result["validation_errors"]) > 0
    assert result["citations"] == []  # Invalid citations strictly discarded
    assert "Citation validation failed" in result["answer"]
    assert "final_response" in result["steps_taken"]
