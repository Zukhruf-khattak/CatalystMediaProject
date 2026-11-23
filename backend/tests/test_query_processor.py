from app.services.query_processor import get_query_processor


def test_query_processor_extract_team_code():
    processor = get_query_processor()
    query = "Team TS3006 planned both an LCD screen and speech recognition."
    res = processor.process_query(query)

    assert res.extracted_team == "TS3006"
    assert "lcd" in res.extracted_topics
    assert "speech recognition" in res.extracted_topics


def test_query_processor_extract_meeting_code():
    processor = get_query_processor()
    query = "In meeting TS3006c, what did they decide about the casing?"
    res = processor.process_query(query)

    assert res.extracted_team == "TS3006"
    assert "ts3006c" in res.extracted_meetings
    assert "casing" in res.extracted_topics or "case" in res.extracted_topics


def test_query_processor_extract_speaker_and_role():
    processor = get_query_processor()
    query = "Speaker B and the Project Manager discussed battery costs."
    res = processor.process_query(query)

    assert "Speaker B" in res.extracted_speakers
    assert "Project Manager" in res.extracted_speakers
    assert "battery" in res.extracted_topics
    assert "cost" in res.extracted_topics or "costs" in res.extracted_topics


def test_query_processor_temporal_intent_detection():
    processor = get_query_processor()

    # Change intent
    res_change = processor.process_query("Why did they switch from titanium to rubber?")
    assert res_change.temporal_intent == "change"

    # Initial intent
    res_initial = processor.process_query("What did the team initially settle on at first?")
    assert res_initial.temporal_intent == "initial"

    # Final intent
    res_final = processor.process_query("What was in their final design in the end?")
    assert res_final.temporal_intent == "final"


def test_query_processor_cleaned_keyword_query():
    processor = get_query_processor()
    query = "What did Team TS3006 decide about the titanium case in their meeting?"
    res = processor.process_query(query)

    # Question stopwords ('what', 'did', 'about', 'the', 'in', 'their') removed
    keywords = res.cleaned_keyword_query.lower()
    assert "titanium" in keywords
    assert "case" in keywords
    assert "what did" not in keywords


def test_query_processor_empty_or_malformed():
    processor = get_query_processor()
    res = processor.process_query("   ")
    assert res.raw_query == ""
    assert res.extracted_team is None
    assert res.cleaned_keyword_query == ""
