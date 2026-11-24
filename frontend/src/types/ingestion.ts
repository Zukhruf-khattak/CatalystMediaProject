export interface IngestionJob {
  id: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | string;
  started_at: string;
  completed_at?: string | null;
  total_files: number;
  completed_meetings: number;
  failed_meetings: number;
  skipped_meetings: number;
  total_turns: number;
  total_words: number;
  embedded_turns: number;
  current_file?: string | null;
  errors_json: Array<Record<string, any>>;
  summary_json: Record<string, any>;
}

export interface IngestionJobListResponse {
  jobs: IngestionJob[];
  total_count: number;
}

export interface IngestionStatsResponse {
  total_teams: number;
  total_meetings: number;
  total_speakers: number;
  total_turns: number;
  embedded_turns: number;
  latest_job?: IngestionJob | null;
}

export interface IngestionJobCreate {
  force_reingest?: boolean;
  skip_embeddings?: boolean;
  limit_files?: number | null;
}

