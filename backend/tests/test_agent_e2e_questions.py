"""End-to-end verification of the LangGraph agent against 5 representative questions from questions.json."""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.agent.service import AgentService
from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn
from app.models.memory import Memory, MemoryStatus, MemoryType
from app.schemas.agent import AgentQueryRequest
from app.services.llm_client import MockLLMClient


def make_test_meeting(team_id: uuid.UUID, code: str, seq: str, num: int) -> Meeting:
    return Meeting(
        id=uuid.uuid4(),
        team_id=team_id,
        meeting_code=code,
        sequence_letter=seq,
        meeting_number=num,
        source_filename=f"{code}.txt",
        source_sha256=f"sha_{code.lower()}",
        raw_text=f"Meeting {code} transcript text",
    )


def make_test_speaker(meeting_id: uuid.UUID, label: str, role: str) -> Speaker:
    letter = label.replace("Speaker ", "").strip()
    return Speaker(
        id=uuid.uuid4(),
        meeting_id=meeting_id,
        speaker_label=label,
        speaker_letter=letter,
        role=role,
    )


def make_test_turn(
    meeting_id: uuid.UUID, speaker_id: uuid.UUID, turn_index: int, seconds: int, text: str
) -> TranscriptTurn:
    mins = seconds // 60
    secs = seconds % 60
    time_str = f"00:{mins:02d}:{secs:02d}"
    return TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=meeting_id,
        speaker_id=speaker_id,
        turn_index=turn_index,
        start_time_str=time_str,
        start_time_seconds=seconds,
        raw_text=text,
        normalized_text=text.lower(),
    )


@pytest.fixture
def benchmark_questions_db(db_session: Session) -> Session:
    """Seed comprehensive cross-meeting test data matching 5 benchmark questions."""

    # -------------------------------------------------------------------------
    # Q01: TS3006 - LCD screen vs Speech Recognition
    # -------------------------------------------------------------------------
    team_ts06 = Team(id=uuid.uuid4(), team_code="TS3006")
    m_ts06b = make_test_meeting(team_ts06.id, "TS3006b", "b", 2)
    m_ts06c = make_test_meeting(team_ts06.id, "TS3006c", "c", 3)
    spk_ts06_pm = make_test_speaker(m_ts06b.id, "Speaker A", "Project Manager")
    spk_ts06_id = make_test_speaker(m_ts06c.id, "Speaker B", "Industrial Designer")
    turn_ts06_1 = make_test_turn(
        m_ts06b.id,
        spk_ts06_pm.id,
        15,
        120,
        "We initially planned to feature both an LCD screen and speech recognition.",
    )
    turn_ts06_2 = make_test_turn(
        m_ts06c.id,
        spk_ts06_id.id,
        45,
        350,
        "Because of component costs we dropped speech recognition and kept the LCD screen.",
    )
    mem_ts06 = Memory(
        id=uuid.uuid4(),
        team_id=team_ts06.id,
        meeting_id=m_ts06c.id,
        turn_id=turn_ts06_2.id,
        memory_type=MemoryType.DECISION.value,
        statement="The team dropped speech recognition due to high component cost and kept the LCD screen.",
        quote="costs we dropped speech recognition and kept the lcd screen",
        speaker_label="Speaker B",
        speaker_role="Industrial Designer",
        meeting_order=3,
        sequence_letter="c",
        status=MemoryStatus.CURRENT.value,
    )
    db_session.add_all(
        [team_ts06, m_ts06b, m_ts06c, spk_ts06_pm, spk_ts06_id, turn_ts06_1, turn_ts06_2, mem_ts06]
    )

    # -------------------------------------------------------------------------
    # Q02: ES2003 - Case material switch (rubber to plastic)
    # -------------------------------------------------------------------------
    team_es03 = Team(id=uuid.uuid4(), team_code="ES2003")
    m_es03b = make_test_meeting(team_es03.id, "ES2003b", "b", 2)
    m_es03d = make_test_meeting(team_es03.id, "ES2003d", "d", 4)
    spk_es03_id = make_test_speaker(m_es03b.id, "Speaker B", "Industrial Designer")
    spk_es03_pm = make_test_speaker(m_es03d.id, "Speaker A", "Project Manager")
    turn_es03_1 = make_test_turn(
        m_es03b.id,
        spk_es03_id.id,
        20,
        180,
        "We leaned towards using double curved rubber casing for the case.",
    )
    turn_es03_2 = make_test_turn(
        m_es03d.id,
        spk_es03_pm.id,
        55,
        420,
        "We switched to standard plastic because rubber moulding was exceeding our cost budget.",
    )
    db_session.add_all(
        [team_es03, m_es03b, m_es03d, spk_es03_id, spk_es03_pm, turn_es03_1, turn_es03_2]
    )

    # -------------------------------------------------------------------------
    # Q03: TS3009 - Titanium back replacement
    # -------------------------------------------------------------------------
    team_ts09 = Team(id=uuid.uuid4(), team_code="TS3009")
    m_ts09b = make_test_meeting(team_ts09.id, "TS3009b", "b", 2)
    m_ts09c = make_test_meeting(team_ts09.id, "TS3009c", "c", 3)
    spk_ts09_id = make_test_speaker(m_ts09b.id, "Speaker B", "Industrial Designer")
    spk_ts09_ui = make_test_speaker(m_ts09c.id, "Speaker C", "User Interface Designer")
    turn_ts09_1 = make_test_turn(
        m_ts09b.id,
        spk_ts09_id.id,
        12,
        90,
        "The concept includes a solid titanium back for the remote casing.",
    )
    turn_ts09_2 = make_test_turn(
        m_ts09c.id,
        spk_ts09_ui.id,
        34,
        260,
        "Speaker C proposed replacing the titanium with recyclable plastic, and titanium was discarded.",
    )
    db_session.add_all(
        [team_ts09, m_ts09b, m_ts09c, spk_ts09_id, spk_ts09_ui, turn_ts09_1, turn_ts09_2]
    )

    # -------------------------------------------------------------------------
    # Q04: TS3011 - Combined energy source
    # -------------------------------------------------------------------------
    team_ts11 = Team(id=uuid.uuid4(), team_code="TS3011")
    m_ts11b = make_test_meeting(team_ts11.id, "TS3011b", "b", 2)
    m_ts11d = make_test_meeting(team_ts11.id, "TS3011d", "d", 4)
    spk_ts11_id = make_test_speaker(m_ts11b.id, "Speaker B", "Industrial Designer")
    turn_ts11_1 = make_test_turn(
        m_ts11b.id,
        spk_ts11_id.id,
        8,
        75,
        "We selected a combination of solar cells and a kinetic dynamo battery.",
    )
    turn_ts11_2 = make_test_turn(
        m_ts11d.id,
        spk_ts11_id.id,
        62,
        510,
        "When the total costs were calculated, the kinetic battery was dropped, keeping standard batteries.",
    )
    db_session.add_all([team_ts11, m_ts11b, m_ts11d, spk_ts11_id, turn_ts11_1, turn_ts11_2])

    # -------------------------------------------------------------------------
    # Q05: TS3008 - Corporate colour scheme
    # -------------------------------------------------------------------------
    team_ts08 = Team(id=uuid.uuid4(), team_code="TS3008")
    m_ts08a = make_test_meeting(team_ts08.id, "TS3008a", "a", 1)
    m_ts08d = make_test_meeting(team_ts08.id, "TS3008d", "d", 4)
    spk_ts08_mkt = make_test_speaker(m_ts08a.id, "Speaker D", "Marketing")
    turn_ts08_1 = make_test_turn(
        m_ts08a.id,
        spk_ts08_mkt.id,
        14,
        105,
        "The company considered using bright yellow corporate branding colours.",
    )
    turn_ts08_2 = make_test_turn(
        m_ts08d.id,
        spk_ts08_mkt.id,
        48,
        380,
        "In the final meeting they chose dark grey because consumers found bright colours unattractive.",
    )
    db_session.add_all([team_ts08, m_ts08a, m_ts08d, spk_ts08_mkt, turn_ts08_1, turn_ts08_2])

    db_session.commit()
    return db_session


def test_e2e_q01_ts3006_lcd_vs_speech(benchmark_questions_db: Session) -> None:
    """Q01: Team TS3006 LCD screen vs speech recognition cut."""
    mock_llm = MockLLMClient(
        canned_response=(
            "When component costs forced a cut, Team TS3006 dropped speech recognition and kept the LCD screen. "
            "They kept the LCD screen because it was essential for the user interface while speech recognition was too expensive."
        )
    )
    service = AgentService(db=benchmark_questions_db, llm_client=mock_llm)
    req = AgentQueryRequest(
        question="Team TS3006 planned both an LCD screen and speech recognition. When the costs forced a cut, which did they drop and which did they keep?",
        team_code="TS3006",
    )
    res = service.query(req)
    assert res.is_sufficient is True
    assert "dropped speech recognition" in res.answer.lower()
    assert "kept the lcd" in res.answer.lower()
    assert len(res.citations) >= 1
    assert any("TS3006" in c.meeting_id for c in res.citations)


def test_e2e_q02_es2003_case_material_switch(benchmark_questions_db: Session) -> None:
    """Q02: Team ES2003 Case material switch from rubber to plastic."""
    mock_llm = MockLLMClient(
        canned_response=(
            "Team ES2003 initially leaned towards a double curved rubber case in ES2003b. "
            "In ES2003d, they switched to standard plastic because rubber moulding exceeded the cost budget."
        )
    )
    service = AgentService(db=benchmark_questions_db, llm_client=mock_llm)
    req = AgentQueryRequest(
        question="Team ES2003 leaned towards one material for the case and then switched to another. What did they lean towards first, what did they end with, and why?",
        team_code="ES2003",
    )
    res = service.query(req)
    assert res.is_sufficient is True
    assert "rubber" in res.answer.lower()
    assert "plastic" in res.answer.lower()
    assert len(res.citations) >= 1


def test_e2e_q03_ts3009_titanium_back_replacement(benchmark_questions_db: Session) -> None:
    """Q03: Team TS3009 Titanium back replacement proposal."""
    mock_llm = MockLLMClient(
        canned_response=(
            "Speaker C first proposed replacing the titanium back with recyclable plastic in TS3009c. "
            "In the end, titanium was discarded and not kept for the final remote."
        )
    )
    service = AgentService(db=benchmark_questions_db, llm_client=mock_llm)
    req = AgentQueryRequest(
        question="Team TS3009 planned a titanium back for their remote. Who first proposed replacing the titanium, what did they propose instead, and was the titanium kept in the end?",
        team_code="TS3009",
    )
    res = service.query(req)
    assert res.is_sufficient is True
    assert "speaker c" in res.answer.lower()
    assert "plastic" in res.answer.lower()
    assert len(res.citations) >= 1


def test_e2e_q04_ts3011_combined_energy_source(benchmark_questions_db: Session) -> None:
    """Q04: Team TS3011 Combined energy source."""
    mock_llm = MockLLMClient(
        canned_response=(
            "Team TS3011 chose a combination of solar cells and a kinetic dynamo battery in TS3011b. "
            "When component costs were added up in TS3011d, the kinetic battery was dropped in favor of standard batteries."
        )
    )
    service = AgentService(db=benchmark_questions_db, llm_client=mock_llm)
    req = AgentQueryRequest(
        question="Team TS3011 chose a combined energy source for their remote. What was the combination, and what happened when costs were added up?",
        team_code="TS3011",
    )
    res = service.query(req)
    assert res.is_sufficient is True
    assert "solar" in res.answer.lower()
    assert "kinetic" in res.answer.lower()
    assert len(res.citations) >= 1


def test_e2e_q05_ts3008_corporate_colour_scheme(benchmark_questions_db: Session) -> None:
    """Q05: Team TS3008 Corporate colour scheme."""
    mock_llm = MockLLMClient(
        canned_response=(
            "Team TS3008 initially considered a bright yellow corporate branding colour in TS3008a. "
            "In meeting TS3008d, they chose dark grey because market feedback showed consumers disliked bright remotes."
        )
    )
    service = AgentService(db=benchmark_questions_db, llm_client=mock_llm)
    req = AgentQueryRequest(
        question="Team TS3008 discussed corporate colour schemes for the remote. What colour did they initially consider, what did they choose in the final meeting, and why?",
        team_code="TS3008",
    )
    res = service.query(req)
    assert res.is_sufficient is True
    assert "yellow" in res.answer.lower()
    assert "grey" in res.answer.lower()
    assert len(res.citations) >= 1
