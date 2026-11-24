export interface TurnItem {
  id: string;
  turn_index: number;
  meeting_id: string;
  speaker_label: string;
  speaker_role?: string | null;
  start_time: string;
  raw_text: string;
  is_target: boolean;
}

export interface TurnContextResponse {
  turn: TurnItem;
  context: TurnItem[];
}
