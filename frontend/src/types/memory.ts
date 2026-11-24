export interface MemoryRelationship {
  id: string;
  source_memory_id: string;
  target_memory_id: string;
  relationship_type: "supports" | "contradicts" | "updates" | "supersedes" | "resolves" | "reopens" | string;
  rationale?: string | null;
  is_ambiguous: boolean;
  confidence: number;
  created_at: string;
}

export interface MemoryResponse {
  id: string;
  team_id: string;
  meeting_id: string;
  turn_id?: string | null;
  memory_type: "DECISION" | "ACTION" | "PREFERENCE" | "REQUIREMENT" | "DISAGREEMENT" | "ENTITY" | string;
  statement: string;
  quote: string;
  speaker_label: string;
  speaker_role?: string | null;
  meeting_order: number;
  sequence_letter: string;
  status: "current" | "superseded" | "open" | "resolved" | "rejected" | string;
  confidence: number;
  extraction_version: string;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
  outgoing_relationships: MemoryRelationship[];
  incoming_relationships: MemoryRelationship[];
}

export interface MemorySearchFilter {
  team_code?: string;
  meeting_code?: string;
  meeting_order?: number;
  sequence_letter?: string;
  memory_type?: string;
  status?: string;
  query_text?: string;
  limit?: number;
  offset?: number;
}

export interface MemorySearchResponse {
  items: MemoryResponse[];
  total_count: number;
  limit: number;
  offset: number;
}
