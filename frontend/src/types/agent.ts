export interface AgentCitationItem {
  meeting_id: string;
  quote: string;
  speaker_label?: string | null;
  speaker_role?: string | null;
  turn_id?: string | null;
  turn_index?: number | null;
}

export interface CitationValidationItem {
  is_valid: boolean;
  meeting_id: string;
  quote: string;
  word_count: number;
  speaker_label?: string | null;
  turn_id?: string | null;
  errors: string[];
}

export interface AnswerValidationResult {
  is_valid: boolean;
  sentence_count: number;
  citation_count: number;
  distinct_meetings: string[];
  supporting_meetings: string[];
  citations: CitationValidationItem[];
  errors: string[];
}

export interface TranscriptEvidenceItem {
  turn_id: string;
  meeting_id: string;
  meeting_code: string;
  meeting_number?: number | null;
  sequence_letter?: string | null;
  turn_index: number;
  speaker_label: string;
  speaker_role?: string | null;
  start_time_str: string;
  raw_text: string;
  score: number;
  retrieval_method: string;
  keyword_rank?: number | null;
  vector_rank?: number | null;
}

export interface MemoryEvidenceItem {
  memory_id: string;
  team_code: string;
  meeting_code: string;
  sequence_letter: string;
  meeting_order: number;
  memory_type: string;
  status: string;
  statement: string;
  quote: string;
  speaker_label: string;
  speaker_role?: string | null;
  turn_id?: string | null;
  confidence: number;
  metadata_json?: Record<string, any>;
  outgoing_relationships?: any[];
  incoming_relationships?: any[];
}

export interface AgentQueryRequest {
  question: string;
  team_code?: string | null;
  session_id?: string | null;
  max_iterations?: number;
}

export interface AgentQueryResponse {
  question: string;
  answer: string;
  is_sufficient: boolean;
  insufficient_reason?: string | null;
  citations: AgentCitationItem[];
  supporting_turns: TranscriptEvidenceItem[];
  supporting_memories: MemoryEvidenceItem[];
  steps_taken: string[];
  session_id: string;
  iteration_count: number;
  team_code?: string | null;
  validation_status: "PASSED" | "FAILED" | "SKIPPED" | string;
  validation_errors: string[];
  supporting_meetings: string[];
  created_at: string;
}

export interface AgentStageEvent {
  stage: string;
  description: string;
  timestamp: string;
  is_sufficient?: boolean;
  citations_count?: number;
}

export interface AgentStatusResponse {
  status: string;
  model_provider: string;
  model_name: string;
  tools_available: string[];
  checkpointer: string;
  langsmith_tracing: boolean;
}
