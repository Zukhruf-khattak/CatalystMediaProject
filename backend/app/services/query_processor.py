import re
from typing import List, Optional, Set

from app.core.logging import get_logger
from app.schemas.retrieval import ProcessedQuery

logger = get_logger("app.services.query_processor")

# Regex for AMI Meeting Corpus team codes (e.g. TS3006, ES2003, IS1008)
TEAM_PATTERN = re.compile(r"\b([ETI]S\d{4})\b", re.IGNORECASE)

# Regex for specific meeting codes (e.g. TS3006a, ES2003c)
MEETING_PATTERN = re.compile(r"\b([ETI]S\d{4}[a-d])\b", re.IGNORECASE)

# Regex for speaker labels
SPEAKER_PATTERN = re.compile(r"\bSpeaker\s+([A-D])\b", re.IGNORECASE)

# Roles commonly mentioned in transcripts and benchmark questions
ROLE_KEYWORDS = {
    "project manager": "Project Manager",
    "industrial designer": "Industrial Designer",
    "user interface": "User Interface Designer",
    "ui designer": "User Interface Designer",
    "marketing": "Marketing",
}

# Domain-specific terms for TV remote control design
DOMAIN_TOPICS = [
    # Materials and enclosure
    "titanium",
    "rubber",
    "plastic",
    "wood",
    "curved",
    "double-curved",
    "double curved",
    "case",
    "casing",
    "material",
    "yellow",
    "blue",
    # Power and energy
    "battery",
    "batteries",
    "kinetic",
    "solar",
    "rechargeable",
    "lithium",
    "energy",
    "power",
    # Display and tech features
    "lcd",
    "screen",
    "display",
    "touch screen",
    "touchscreen",
    "speech recognition",
    "voice recognition",
    "voice",
    "buttons",
    "navigation",
    "scroll wheel",
    # Cost, budget, price
    "budget",
    "cost",
    "costs",
    "price",
    "pricing",
    "expensive",
    "euro",
    "euros",
    # Special features
    "lost",
    "locater",
    "locator",
    "find",
    "beep",
    "beeper",
    "fruit",
    "vegetable",
]

# Temporal intent indicator keywords
TEMPORAL_INTENT_MAP = {
    "change": [
        "switch",
        "switched",
        "change",
        "changed",
        "replaced",
        "replace",
        "drop",
        "dropped",
        "reverse",
        "reversed",
        "instead of",
        "instead",
    ],
    "initial": [
        "first",
        "initially",
        "earliest",
        "original",
        "originally",
        "lean towards",
        "leaned towards",
        "at first",
        "start",
    ],
    "final": [
        "final",
        "ended with",
        "end with",
        "settle on",
        "settled on",
        "last",
        "keep",
        "kept",
    ],
    "conflict": [
        "disagreement",
        "objection",
        "conflict",
        "debate",
        "oppose",
        "opposed",
        "argued",
    ],
    "cost": [
        "cost",
        "costs",
        "budget",
        "costing",
        "price",
        "pricing",
        "expensive",
    ],
}

# Stopwords and question phrasing to strip from keyword queries
QUESTION_STOPWORDS: Set[str] = {
    "what",
    "which",
    "who",
    "why",
    "how",
    "when",
    "where",
    "is",
    "was",
    "were",
    "are",
    "did",
    "do",
    "does",
    "the",
    "a",
    "an",
    "in",
    "on",
    "at",
    "of",
    "to",
    "for",
    "from",
    "by",
    "with",
    "and",
    "or",
    "that",
    "this",
    "their",
    "they",
    "them",
    "it",
    "its",
    "about",
    "one",
    "two",
    "three",
    "four",
    "team",
    "meeting",
    "meetings",
    "planned",
    "would",
    "could",
    "should",
    "said",
    "report",
    "reported",
    "come",
    "back",
    "reach",
    "reached",
}


class QueryProcessor:
    """Deterministic parser extracting entities, teams, speakers, topics, and keyword queries."""

    def process_query(self, raw_query: str) -> ProcessedQuery:
        """Analyze query string and return structured ProcessedQuery."""
        if not raw_query or not raw_query.strip():
            return ProcessedQuery(
                raw_query="",
                cleaned_keyword_query="",
            )

        query_text = raw_query.strip()
        lower_query = query_text.lower()

        # 1. Extract Team Code
        team_match = TEAM_PATTERN.search(query_text)
        extracted_team = team_match.group(1).upper() if team_match else None

        # 2. Extract Specific Meeting Codes
        extracted_meetings = [m.lower() for m in MEETING_PATTERN.findall(query_text)]

        # If team code was not directly matched as a standalone 6-char token, infer from meeting code
        if not extracted_team and extracted_meetings:
            extracted_team = extracted_meetings[0][:6].upper()

        # 3. Extract Speakers and Roles
        extracted_speakers: List[str] = []
        for spk in SPEAKER_PATTERN.finditer(query_text):
            extracted_speakers.append(f"Speaker {spk.group(1).upper()}")

        for role_key, role_name in ROLE_KEYWORDS.items():
            if role_key in lower_query and role_name not in extracted_speakers:
                extracted_speakers.append(role_name)

        # 4. Extract Domain Topics
        extracted_topics: List[str] = []
        for topic in DOMAIN_TOPICS:
            if topic in lower_query and topic not in extracted_topics:
                extracted_topics.append(topic)

        # 5. Detect Temporal Intent
        temporal_intent: Optional[str] = None
        for intent, triggers in TEMPORAL_INTENT_MAP.items():
            if any(trig in lower_query for trig in triggers):
                temporal_intent = intent
                break

        # 6. Build Cleaned Keyword Query
        # Tokenize, strip punctuation and question stopwords
        tokens = re.findall(r"\b[A-Za-z0-9\-\_]{2,}\b", query_text)
        filtered_tokens = []
        for token in tokens:
            low = token.lower()
            # Skip team codes and meeting codes in keywords if we already filter by team
            if extracted_team and low == extracted_team.lower():
                continue
            if any(low == m.lower() for m in extracted_meetings):
                continue
            if low not in QUESTION_STOPWORDS:
                filtered_tokens.append(token)

        cleaned_keyword_query = " ".join(filtered_tokens) if filtered_tokens else query_text

        logger.debug(
            f"Processed query '{raw_query[:50]}...': Team={extracted_team}, "
            f"Topics={extracted_topics}, Intent={temporal_intent}"
        )

        return ProcessedQuery(
            raw_query=raw_query,
            cleaned_keyword_query=cleaned_keyword_query,
            extracted_team=extracted_team,
            extracted_meetings=extracted_meetings,
            extracted_speakers=extracted_speakers,
            extracted_topics=extracted_topics,
            temporal_intent=temporal_intent,
        )


_query_processor_instance: Optional[QueryProcessor] = None


def get_query_processor() -> QueryProcessor:
    """Return singleton QueryProcessor instance."""
    global _query_processor_instance
    if _query_processor_instance is None:
        _query_processor_instance = QueryProcessor()
    return _query_processor_instance
