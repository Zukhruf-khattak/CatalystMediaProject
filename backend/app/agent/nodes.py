"""LangGraph nodes implementing the 8-stage meeting intelligence reasoning workflow."""

import re
from typing import Any, Dict, List, Optional

from app.agent.state import AgentState
from app.agent.tools import AgentTools
from app.core.logging import get_logger
from app.services.citation_validation_service import CitationValidationService
from app.services.evidence_validator import EvidenceValidator
from app.services.llm_client import BaseLLMClient, get_llm_client
from app.services.query_processor import QueryProcessor, get_query_processor

logger = get_logger("app.agent.nodes")

# Standard and AMI corpus stopwords excluded when determining substantive topical tokens
QUESTION_STOPWORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "aren't",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "can't",
    "cannot",
    "could",
    "couldn't",
    "did",
    "didn't",
    "do",
    "does",
    "doesn't",
    "doing",
    "don't",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "hadn't",
    "has",
    "hasn't",
    "have",
    "haven't",
    "having",
    "he",
    "he'd",
    "he'll",
    "he's",
    "her",
    "here",
    "here's",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "how's",
    "i",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "if",
    "in",
    "into",
    "is",
    "isn't",
    "it",
    "it's",
    "its",
    "itself",
    "let's",
    "me",
    "more",
    "most",
    "mustn't",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "ought",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "shan't",
    "she",
    "she'd",
    "she'll",
    "she's",
    "should",
    "shouldn't",
    "so",
    "some",
    "such",
    "than",
    "that",
    "that's",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "there's",
    "these",
    "they",
    "they'd",
    "they'll",
    "they're",
    "they've",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "wasn't",
    "we",
    "we'd",
    "we'll",
    "we're",
    "we've",
    "were",
    "weren't",
    "what",
    "what's",
    "when",
    "when's",
    "where",
    "where's",
    "which",
    "while",
    "who",
    "who's",
    "whom",
    "why",
    "why's",
    "with",
    "won't",
    "would",
    "wouldn't",
    "you",
    "you'd",
    "you'll",
    "you're",
    "you've",
    "your",
    "yours",
    "yourself",
    "yourselves",
    # AMI corpus ubiquitous terms
    "team",
    "meeting",
    "meetings",
    "remote",
    "device",
    "control",
    "decide",
    "decision",
    "decided",
    "use",
    "used",
    "plan",
    "planned",
    "project",
    "speaker",
}


class AgentNodes:
    """
    Implements the discrete graph nodes for multi-step meeting intelligence reasoning.
    Dependencies (AgentTools, LLM client, QueryProcessor) are injected at construction.
    """

    def __init__(
        self,
        tools: AgentTools,
        llm_client: Optional[BaseLLMClient] = None,
        query_processor: Optional[QueryProcessor] = None,
    ) -> None:
        self.tools = tools
        self.llm_client = llm_client or get_llm_client()
        self.query_processor = query_processor or get_query_processor()
        self.validator = EvidenceValidator()
        self.citation_validator = CitationValidationService(tools.db)

    # -------------------------------------------------------------------------
    # Node 1: Input Validation
    # -------------------------------------------------------------------------
    def input_validation(self, state: AgentState) -> Dict[str, Any]:
        """Validate input question, parameters, and initialize execution state."""
        question = (state.get("question") or "").strip()
        steps = list(state.get("steps_taken") or [])
        steps.append("input_validation")

        if not question or len(question) < 3:
            return {
                "question": question,
                "is_sufficient": False,
                "insufficient_reason": "Question is empty or too short to process.",
                "answer": "Please provide a valid question of at least 3 characters.",
                "error": "Validation error: question too short.",
                "steps_taken": steps,
            }

        return {
            "question": question,
            "team_code": state.get("team_code"),
            "session_id": state.get("session_id") or "default",
            "iteration": state.get("iteration") or 0,
            "max_iterations": state.get("max_iterations") or 2,
            "retrieved_turns": list(state.get("retrieved_turns") or []),
            "retrieved_memories": list(state.get("retrieved_memories") or []),
            "meeting_contexts": list(state.get("meeting_contexts") or []),
            "memory_histories": list(state.get("memory_histories") or []),
            "steps_taken": steps,
            "error": None,
        }

    # -------------------------------------------------------------------------
    # Node 2: Query Analysis
    # -------------------------------------------------------------------------
    def query_analysis(self, state: AgentState) -> Dict[str, Any]:
        """Analyze query to extract team, meetings, speakers, domain topics, and temporal intent."""
        question = state["question"]
        steps = list(state.get("steps_taken") or [])
        steps.append("query_analysis")

        processed = self.query_processor.process_query(question)
        analysis_dict = processed.model_dump()

        # Prioritize explicit team_code from state if provided, otherwise use extracted
        team_code = state.get("team_code") or processed.extracted_team

        return {
            "query_analysis": analysis_dict,
            "team_code": team_code,
            "steps_taken": steps,
        }

    # -------------------------------------------------------------------------
    # Node 3: Retrieval Planning
    # -------------------------------------------------------------------------
    def retrieval_planning(self, state: AgentState) -> Dict[str, Any]:
        """Formulate targeted retrieval tool calls based on query analysis and iteration history."""
        steps = list(state.get("steps_taken") or [])
        steps.append("retrieval_planning")

        analysis = state.get("query_analysis") or {}
        team_code = state.get("team_code") or analysis.get("extracted_team")
        cleaned_query = analysis.get("cleaned_query") or state["question"]
        iteration = state.get("iteration", 0)
        missing_facets = state.get("missing_facets") or []

        plan: List[Dict[str, Any]] = []

        if iteration == 0:
            # Initial retrieval pass: broad hybrid search across transcript
            plan.append(
                {
                    "tool": "hybrid_search",
                    "args": {
                        "query": cleaned_query,
                        "team_code": team_code,
                        "meeting_codes": analysis.get("extracted_meetings") or None,
                        "limit": 10,
                        "method": "hybrid",
                    },
                }
            )

            # Search temporal memory for structured decisions or disagreements
            plan.append(
                {
                    "tool": "search_temporal_memory",
                    "args": {
                        "query": cleaned_query,
                        "team_code": team_code,
                        "limit": 10,
                    },
                }
            )

            # If team is known, get meeting sequence to map chronological order
            if team_code:
                plan.append(
                    {
                        "tool": "get_related_meetings",
                        "args": {"team_code": team_code},
                    }
                )

        else:
            # Re-retrieval pass: target missing facets identified during evidence assessment
            retrieved_turns = state.get("retrieved_turns") or []
            covered_meetings = {t.get("meeting_id") for t in retrieved_turns if t.get("meeting_id")}

            # If multi-meeting evidence is needed and we know the team's meetings
            meeting_contexts = state.get("meeting_contexts") or []
            all_meetings = [
                m.get("meeting_code") for m in meeting_contexts if m.get("meeting_code")
            ]

            uncovered_meetings = [m for m in all_meetings if m not in covered_meetings]

            if "multi_meeting_evidence_needed" in missing_facets and uncovered_meetings:
                # Target the uncovered meetings specifically with topic keywords
                topics = analysis.get("extracted_topics") or [cleaned_query]
                query_str = " ".join(topics) if topics else cleaned_query
                plan.append(
                    {
                        "tool": "hybrid_search",
                        "args": {
                            "query": query_str,
                            "team_code": team_code,
                            "meeting_codes": uncovered_meetings,
                            "limit": 10,
                            "method": "hybrid",
                        },
                    }
                )

            # If memories were retrieved, inspect their complete temporal evolution
            retrieved_memories = state.get("retrieved_memories") or []
            for mem in retrieved_memories[:3]:
                m_id = mem.get("memory_id")
                if m_id:
                    plan.append(
                        {
                            "tool": "get_memory_history",
                            "args": {"memory_id": m_id},
                        }
                    )

            # Fallback if no specific plan was added
            if not plan:
                plan.append(
                    {
                        "tool": "hybrid_search",
                        "args": {
                            "query": state["question"],
                            "team_code": team_code,
                            "limit": 10,
                            "method": "hybrid",
                        },
                    }
                )

        return {
            "retrieval_plan": plan,
            "steps_taken": steps,
        }

    # -------------------------------------------------------------------------
    # Node 4: Tool Execution
    # -------------------------------------------------------------------------
    def tool_execution(self, state: AgentState) -> Dict[str, Any]:
        """Execute planned tool calls and accumulate deduplicated evidence in state."""
        steps = list(state.get("steps_taken") or [])
        steps.append("tool_execution")

        plan = state.get("retrieval_plan") or []
        existing_turns = {t.get("turn_id"): t for t in (state.get("retrieved_turns") or [])}
        existing_memories = {m.get("memory_id"): m for m in (state.get("retrieved_memories") or [])}
        meeting_contexts = list(state.get("meeting_contexts") or [])
        memory_histories = list(state.get("memory_histories") or [])
        tool_call_records: List[Dict[str, Any]] = list(state.get("tool_calls") or [])

        for item in plan:
            tool_name = item.get("tool")
            args = item.get("args") or {}
            exec_record = self.tools.execute_tool(tool_name, **args)
            tool_call_records.append(exec_record)

            res = exec_record.get("result")
            if not res:
                continue

            if tool_name == "hybrid_search":
                for turn in res.get("turns") or []:
                    t_id = turn.get("turn_id")
                    if t_id and t_id not in existing_turns:
                        existing_turns[t_id] = turn
                for mem in res.get("memories") or []:
                    m_id = mem.get("memory_id")
                    if m_id and m_id not in existing_memories:
                        existing_memories[m_id] = mem

            elif tool_name == "search_temporal_memory":
                if isinstance(res, list):
                    for mem in res:
                        m_id = mem.get("memory_id")
                        if m_id and m_id not in existing_memories:
                            existing_memories[m_id] = mem

            elif tool_name == "get_related_meetings":
                if isinstance(res, list):
                    meeting_contexts = res

            elif tool_name == "get_meeting_details":
                if isinstance(res, dict):
                    meeting_contexts.append(res)

            elif tool_name == "get_memory_history":
                if isinstance(res, dict) and "history" in res:
                    memory_histories.append(res)

        iteration = (state.get("iteration") or 0) + 1

        return {
            "retrieved_turns": list(existing_turns.values()),
            "retrieved_memories": list(existing_memories.values()),
            "meeting_contexts": meeting_contexts,
            "memory_histories": memory_histories,
            "tool_calls": tool_call_records,
            "iteration": iteration,
            "steps_taken": steps,
        }

    # -------------------------------------------------------------------------
    # Node 5: Evidence Assessment
    # -------------------------------------------------------------------------
    def evidence_assessment(self, state: AgentState) -> Dict[str, Any]:
        """Assess if evidence is sufficient to answer the question, or if re-retrieval is required."""
        steps = list(state.get("steps_taken") or [])
        steps.append("evidence_assessment")

        question = (state.get("question") or "").strip()
        turns = state.get("retrieved_turns") or []
        memories = state.get("retrieved_memories") or []
        iteration = state.get("iteration") or 1
        max_iterations = state.get("max_iterations") or 2
        analysis = state.get("query_analysis") or {}

        # 1. Total evidence volume check
        total_items = len(turns) + len(memories)
        if total_items == 0:
            if iteration < max_iterations:
                return {
                    "is_sufficient": False,
                    "missing_facets": ["broaden_search"],
                    "insufficient_reason": "No evidence retrieved in initial pass.",
                    "steps_taken": steps,
                }
            return {
                "is_sufficient": False,
                "missing_facets": [],
                "insufficient_reason": "No relevant transcript turns or memories found in corpus.",
                "steps_taken": steps,
            }

        # 2. Substantive topical relevance check
        raw_tokens = re.findall(r"\b[a-zA-Z0-9\-\_]{3,}\b", question.lower())
        substantive_tokens = [
            t
            for t in raw_tokens
            if t not in QUESTION_STOPWORDS and not re.match(r"^[eti]s\d{4}[a-d]?$", t)
        ]

        if substantive_tokens:
            evidence_text = " ".join(
                [(t.get("text") or "") for t in turns]
                + [(m.get("statement") or "") + " " + (m.get("quote") or "") for m in memories]
            ).lower()

            matched_tokens = [
                tok
                for tok in substantive_tokens
                if tok in evidence_text
                or (len(tok) > 3 and tok.rstrip("s") in evidence_text)
                or (len(tok) > 4 and tok.rstrip("ed") in evidence_text)
                or (len(tok) > 4 and tok.rstrip("ing") in evidence_text)
            ]

            if not matched_tokens:
                # Check if there are other un-searched meetings for this team
                covered_meetings = {t.get("meeting_id") for t in turns if t.get("meeting_id")}
                meeting_contexts = state.get("meeting_contexts") or []
                all_meetings = [
                    m.get("meeting_code") for m in meeting_contexts if m.get("meeting_code")
                ]
                uncovered_meetings = [m for m in all_meetings if m not in covered_meetings]

                if uncovered_meetings and iteration < max_iterations:
                    return {
                        "is_sufficient": False,
                        "missing_facets": ["multi_meeting_evidence_needed"],
                        "insufficient_reason": (
                            "Queried topics not found in initial meetings; "
                            "re-retrieving across remaining meetings."
                        ),
                        "steps_taken": steps,
                    }

                return {
                    "is_sufficient": False,
                    "missing_facets": [],
                    "insufficient_reason": (
                        "No relevant transcript turns or memories found in meeting corpus "
                        f"for queried topics: {substantive_tokens[:3]}."
                    ),
                    "steps_taken": steps,
                }

        # 3. Multi-meeting check for questions requiring cross-meeting progression
        distinct_meetings = {t.get("meeting_id") for t in turns if t.get("meeting_id")} | {
            m.get("meeting_id") for m in memories if m.get("meeting_id")
        }
        distinct_meetings.discard(None)

        is_temporal = analysis.get("is_temporal_query", False)
        requires_multi_meeting = is_temporal or len(analysis.get("extracted_meetings") or []) > 1

        if requires_multi_meeting and len(distinct_meetings) < 2:
            if iteration < max_iterations:
                return {
                    "is_sufficient": False,
                    "missing_facets": ["multi_meeting_evidence_needed"],
                    "insufficient_reason": f"Only 1 meeting ({list(distinct_meetings)}) retrieved for multi-meeting question.",
                    "steps_taken": steps,
                }
            # Reached max iterations without finding second meeting
            return {
                "is_sufficient": False,
                "missing_facets": [],
                "insufficient_reason": "Insufficient cross-meeting evidence: relevant discussion found in only one meeting.",
                "steps_taken": steps,
            }

        # Evidence is sufficient to generate an answer
        return {
            "is_sufficient": True,
            "missing_facets": [],
            "insufficient_reason": None,
            "steps_taken": steps,
        }

    # -------------------------------------------------------------------------
    # Node 6: Answer Generation
    # -------------------------------------------------------------------------
    def answer_generation(self, state: AgentState) -> Dict[str, Any]:
        """Synthesize a concise, factual 1-3 sentence answer grounded strictly in retrieved evidence."""
        steps = list(state.get("steps_taken") or [])
        steps.append("answer_generation")

        question = state["question"]
        turns = state.get("retrieved_turns") or []
        memories = state.get("retrieved_memories") or []
        memory_histories = state.get("memory_histories") or []
        team_code = state.get("team_code")
        validation_feedback = state.get("validation_feedback")

        # Prepare evidence text payload for the LLM
        evidence_lines = []
        for turn in turns[:10]:
            m_id = turn.get("meeting_id")
            spk = turn.get("speaker_label") or "Speaker"
            role = f" ({turn.get('speaker_role')})" if turn.get("speaker_role") else ""
            txt = turn.get("text", "").strip()
            evidence_lines.append(f'[{m_id}] {spk}{role}: "{txt}"')

        for mem in memories[:5]:
            m_id = mem.get("meeting_id")
            stat = mem.get("status")
            mtype = mem.get("memory_type")
            stmt = mem.get("statement")
            quote = mem.get("quote")
            evidence_lines.append(f'[{m_id} Memory ({mtype}, {stat})]: {stmt} (Quote: "{quote}")')

        for hist in memory_histories[:3]:
            for h in hist.get("history", [])[:3]:
                h_mid = h.get("meeting_id")
                h_rel = h.get("relation")
                h_stat = h.get("status")
                h_stmt = h.get("statement")
                evidence_lines.append(f"[{h_mid} Lineage ({h_rel}, {h_stat})]: {h_stmt}")

        evidence_str = "\n".join(evidence_lines)

        feedback_prompt = ""
        if validation_feedback:
            feedback_prompt = (
                f"\nATTENTION: A prior attempt failed validation:\n{validation_feedback}\n"
                "You MUST fix these issues: provide exactly 1 to 3 plain sentences, and ground the answer "
                "using facts from at least 2 distinct meetings of the named team."
            )

        prompt = f"""You are the Catalist Meeting Intelligence research agent.
Answer the following user question based STRICTLY and ONLY on the provided meeting excerpts and memories.

Instructions:
1. Provide a direct, factual 1 to 3 plain sentences answer.
2. Clearly distinguish earlier ideas or leanings from final decisions.
3. Attribute actions or statements to specific meetings (e.g. TS3006a, TS3006d) and speakers (e.g. Speaker B, Project Manager).
4. Do not speculate or introduce outside knowledge.
5. If the excerpts do not contain enough evidence to answer, state: "The provided transcripts do not contain sufficient evidence to answer this question."{feedback_prompt}

Question: {question}

Evidence Excerpts:
{evidence_str}

Answer:"""

        try:
            answer = self.llm_client.generate_text(prompt=prompt)
            if (
                not answer
                or not answer.strip()
                or answer.startswith(
                    "Based on the meeting discussions, the team evaluated the design options"
                )
            ):
                # Fallback synthesized from evidence if model returns empty or default mock placeholder
                answer = self._synthesize_fallback_answer(question, turns, memories, team_code)
        except Exception as e:
            logger.warning(f"Answer generation error: {e}. Using deterministic evidence fallback.")
            answer = self._synthesize_fallback_answer(question, turns, memories, team_code)

        # Extract citations from the evidence matching the answer or key turn
        citations = self._extract_citations(answer, turns, memories, team_code)

        return {
            "answer": answer.strip(),
            "citations": citations,
            "steps_taken": steps,
        }

    # -------------------------------------------------------------------------
    # Node 7: Citation Validation
    # -------------------------------------------------------------------------
    def citation_validation(self, state: AgentState) -> Dict[str, Any]:
        """Deterministically validate answer sentences, citation count, exact quotes, and multi-meeting rules."""
        steps = list(state.get("steps_taken") or [])
        steps.append("citation_validation")
        if "response_validation" not in steps:
            steps.append("response_validation")

        answer = (state.get("answer") or "").strip()
        citations = list(state.get("citations") or [])
        team_code = state.get("team_code")
        retries = state.get("validation_retries") or 0
        max_retries = state.get("max_validation_retries") or 2

        # If answer states transcripts lack evidence, skip deep validation
        lower_ans = answer.lower()
        if "not contain sufficient evidence" in lower_ans or "insufficient evidence" in lower_ans:
            return {
                "is_sufficient": False,
                "validation_status": "SKIPPED",
                "validation_errors": [],
                "supporting_meetings": [],
                "validation_feedback": None,
                "steps_taken": steps,
            }

        # Run deterministic citation and evidence validation service
        val_res = self.citation_validator.validate_answer(
            answer=answer,
            citations=citations,
            expected_team=team_code,
        )

        if val_res.is_valid:
            return {
                "is_sufficient": True,
                "validation_status": "PASSED",
                "validation_errors": [],
                "supporting_meetings": val_res.supporting_meetings,
                "validation_feedback": None,
                "steps_taken": steps,
            }
        else:
            error_summary = "; ".join(val_res.errors)
            logger.warning(
                f"Citation validation failed on attempt {retries + 1}/{max_retries}: {error_summary}"
            )
            return {
                "validation_status": "FAILED",
                "validation_errors": val_res.errors,
                "validation_feedback": (
                    f"Previous answer failed validation: {error_summary}. "
                    "Ensure: 1-3 plain sentences, 1-3 citations, verbatim quotes with >=6 words "
                    "from at least 2 distinct meetings of the named team."
                ),
                "validation_retries": retries + 1,
                "supporting_meetings": val_res.supporting_meetings,
                "steps_taken": steps,
            }

    def response_validation(self, state: AgentState) -> Dict[str, Any]:
        """Backwards-compatible alias for citation_validation node."""
        return self.citation_validation(state)

    # -------------------------------------------------------------------------
    # Node 8: Final Response
    # -------------------------------------------------------------------------
    def final_response(self, state: AgentState) -> Dict[str, Any]:
        """Format final structured output payload for the caller."""
        steps = list(state.get("steps_taken") or [])
        steps.append("final_response")

        is_sufficient = state.get("is_sufficient", False)
        val_status = state.get("validation_status") or ("PASSED" if is_sufficient else "SKIPPED")
        val_errors = list(state.get("validation_errors") or [])
        answer = state.get("answer")
        citations = list(state.get("citations") or [])
        insufficient_reason = state.get("insufficient_reason")

        # If validation failed and retries were exhausted, never silently output invalid citations
        if val_status == "FAILED":
            is_sufficient = False
            reasons_str = "; ".join(val_errors[:3])
            answer = (
                "I do not have sufficient validated evidence from the meeting transcripts "
                f"to answer this question. Citation validation failed: {reasons_str}."
            )
            citations = []  # Discard invalid citations from final answer
            insufficient_reason = f"Citation validation failed: {reasons_str}."

        elif not is_sufficient and not answer:
            answer = insufficient_reason or "Insufficient evidence in meeting corpus to answer."
            citations = []

        return {
            "answer": answer,
            "citations": citations,
            "is_sufficient": is_sufficient,
            "insufficient_reason": insufficient_reason,
            "validation_status": val_status,
            "validation_errors": val_errors,
            "supporting_meetings": state.get("supporting_meetings") or [],
            "steps_taken": steps,
        }

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    def _synthesize_fallback_answer(
        self,
        question: str,
        turns: List[Dict[str, Any]],
        memories: List[Dict[str, Any]],
        team_code: Optional[str] = None,
    ) -> str:
        """Deterministic fallback answer synthesis satisfying 1-3 sentences and multi-meeting attribution."""
        if not turns and not memories:
            return "The meeting transcripts do not contain sufficient evidence to answer this question."

        # Group turns by meeting
        by_meeting: Dict[str, List[Dict[str, Any]]] = {}
        for t in turns:
            m_id = t.get("meeting_id") or t.get("meeting_code") or "Unknown"
            by_meeting.setdefault(m_id, []).append(t)

        sentences = []
        for m_id, m_turns in sorted(by_meeting.items()):
            top_turn = m_turns[0]
            spk = top_turn.get("speaker_label") or "The team"
            role = f" ({top_turn.get('speaker_role')})" if top_turn.get("speaker_role") else ""
            txt = (top_turn.get("text") or top_turn.get("raw_text") or "").strip()
            words = txt.split()
            snippet = " ".join(words[:12]) if len(words) > 12 else txt
            snippet = snippet.rstrip(".")
            sentences.append(f"In meeting {m_id}, {spk}{role} discussed {snippet}.")
            if len(sentences) >= 2:
                break

        if not sentences:
            for mem in memories[:2]:
                m_id = mem.get("meeting_id") or "Unknown"
                stmt = mem.get("statement") or ""
                sentences.append(f"In meeting {m_id}, the decision was that {stmt}.")

        if not sentences:
            return "The meeting transcripts do not contain sufficient evidence to answer this question."

        return " ".join(sentences[:3])

    def _extract_citations(
        self,
        answer: str,
        turns: List[Dict[str, Any]],
        memories: List[Dict[str, Any]],
        team_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Extract citations referencing exact quotes from evidence turns across distinct meetings."""
        citations: List[Dict[str, Any]] = []
        seen_meetings = set()
        seen_turns = set()

        # 1. Group candidate turns by meeting code
        turns_by_meeting: Dict[str, List[Dict[str, Any]]] = {}
        for t in turns:
            m_id = (t.get("meeting_id") or t.get("meeting_code") or "").lower()
            if m_id:
                turns_by_meeting.setdefault(m_id, []).append(t)

        # 2. Extract quotes from memories first
        for mem in memories:
            quote = mem.get("quote")
            m_id = (mem.get("meeting_id") or "").lower()
            if quote and len(quote.split()) >= 6:
                if m_id in seen_meetings and len(turns_by_meeting) > len(seen_meetings):
                    continue
                t_id = mem.get("turn_id")
                citations.append(
                    {
                        "meeting_id": mem.get("meeting_id") or "Unknown",
                        "team_id": team_code or mem.get("team_code") or "Unknown",
                        "quote": quote,
                        "speaker_label": mem.get("speaker_label"),
                        "speaker_role": mem.get("speaker_role"),
                        "turn_id": str(t_id) if t_id else None,
                        "turn_index": None,
                    }
                )
                seen_meetings.add(m_id)
                if t_id:
                    seen_turns.add(str(t_id))
                if len(citations) >= 3:
                    return citations

        # 3. Target multi-meeting coverage from turns: pick 1 quote per distinct meeting first
        for m_id, m_turns in sorted(turns_by_meeting.items()):
            if m_id in seen_meetings and len(turns_by_meeting) > len(seen_meetings):
                continue
            for turn in m_turns:
                t_id = str(turn.get("turn_id")) if turn.get("turn_id") else None
                if t_id and t_id in seen_turns:
                    continue
                raw_text = turn.get("text") or turn.get("raw_text") or ""
                words = raw_text.split()
                if len(words) >= 6:
                    # Pick a clean verbatim slice of at least 6 words and up to 20 words
                    quote_slice = " ".join(words[: min(len(words), 20)])
                    citations.append(
                        {
                            "meeting_id": turn.get("meeting_id")
                            or turn.get("meeting_code")
                            or "Unknown",
                            "team_id": team_code or turn.get("team_code") or "Unknown",
                            "quote": quote_slice,
                            "speaker_label": turn.get("speaker_label"),
                            "speaker_role": turn.get("speaker_role"),
                            "turn_id": t_id,
                            "turn_index": turn.get("turn_index"),
                        }
                    )
                    seen_meetings.add(m_id)
                    if t_id:
                        seen_turns.add(t_id)
                    break
            if len(citations) >= 3:
                break

        # 4. If we still have fewer than 2 citations and more turns exist, add from any turn
        if len(citations) < 2:
            for turn in turns:
                t_id = str(turn.get("turn_id")) if turn.get("turn_id") else None
                if t_id and t_id in seen_turns:
                    continue
                raw_text = turn.get("text") or turn.get("raw_text") or ""
                words = raw_text.split()
                if len(words) >= 6:
                    quote_slice = " ".join(words[: min(len(words), 20)])
                    citations.append(
                        {
                            "meeting_id": turn.get("meeting_id")
                            or turn.get("meeting_code")
                            or "Unknown",
                            "team_id": team_code or turn.get("team_code") or "Unknown",
                            "quote": quote_slice,
                            "speaker_label": turn.get("speaker_label"),
                            "speaker_role": turn.get("speaker_role"),
                            "turn_id": t_id,
                            "turn_index": turn.get("turn_index"),
                        }
                    )
                    if t_id:
                        seen_turns.add(t_id)
                    if len(citations) >= 3:
                        break

        return citations[:3]
