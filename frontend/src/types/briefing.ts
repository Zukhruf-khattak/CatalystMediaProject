export interface BriefingCitation {
  meeting_id: string;
  quote: string;
  speaker_label?: string | null;
  speaker_role?: string | null;
  turn_id?: string | null;
  turn_index?: number | null;
}

export interface TimelineMeetingItem {
  meeting_code: string;
  sequence_letter: string;
  meeting_order: number;
  discussion_topics: string[];
  major_decisions: string[];
  significant_changes: string[];
  open_actions: string[];
  citations: BriefingCitation[];
}

export interface DecisionItem {
  statement: string;
  meeting_id: string;
  speaker_label?: string | null;
  speaker_role?: string | null;
  quote: string;
  status: string;
  replaces_statement?: string | null;
  replaces_meeting_id?: string | null;
  turn_id?: string | null;
}

export interface DecisionChangeItem {
  previous_decision: string;
  updated_decision: string;
  previous_meeting_id: string;
  updated_meeting_id: string;
  previous_quote: string;
  updated_quote: string;
  reason?: string | null;
  turn_id_previous?: string | null;
  turn_id_updated?: string | null;
}

export interface ActionItem {
  description: string;
  owner: string;
  owner_confidence: string;
  source_meeting_id: string;
  speaker_label?: string | null;
  status: string;
  quote: string;
  turn_id?: string | null;
}

export interface DisagreementItem {
  disputed_issue: string;
  positions: string[];
  speakers_involved: string[];
  supporting_evidence: string[];
  resolution_status: string;
  citations: BriefingCitation[];
}

export interface BriefingGenerateRequest {
  team_code: string;
  target_meeting_code?: string | null;
  regenerate?: boolean;
}

export interface BriefingResponse {
  id: string;
  team_code: string;
  target_meeting_code?: string | null;
  version: number;
  title: string;
  content_markdown: string;
  structured_payload: {
    team_metadata?: {
      team_code: string;
      target_meeting: string;
      meetings_covered: string[];
      generated_at: string;
    };
    meetings_timeline?: TimelineMeetingItem[];
    current_decisions?: DecisionItem[];
    decision_changes?: DecisionChangeItem[];
    open_actions?: ActionItem[];
    unresolved_disagreements?: DisagreementItem[];
    confirmed_requirements?: Array<{ requirement: string; meeting_id: string; quote: string }>;
    key_entities?: Record<string, string>;
    summary?: string;
  };
  validation_status: "PASSED" | "FAILED" | "WARNING" | string;
  validation_errors: string[];
  citations_count: number;
  meetings_covered: string[];
  generation_metadata: Record<string, any>;
  created_at: string;
}

export interface BriefingListResponse {
  briefings: BriefingResponse[];
  total: number;
}
