import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DecisionTimelinePage } from "../pages/DecisionTimelinePage";
import * as api from "../lib/api";

vi.mock("../lib/api", () => ({
  fetchLatestBriefing: vi.fn(),
  fetchTurnContext: vi.fn(),
}));

const mockTimelineBriefing = {
  id: "briefing-ts3012",
  team_code: "TS3012",
  target_meeting_code: "TS3012d",
  version: 1,
  title: "Team TS3012 Pre-Meeting Briefing",
  content_markdown: "Timeline markdown",
  structured_payload: {
    meetings_timeline: [
      {
        meeting_code: "TS3012a",
        sequence_letter: "a",
        meeting_order: 1,
        discussion_topics: ["Project Kickoff", "Budget Constraints"],
        major_decisions: ["Target cost under 25 EUR"],
        significant_changes: [],
        open_actions: [],
        citations: [],
      },
      {
        meeting_code: "TS3012b",
        sequence_letter: "b",
        meeting_order: 2,
        discussion_topics: ["Component Layout", "LCD Display"],
        major_decisions: ["Include double LCD display"],
        significant_changes: [],
        open_actions: [],
        citations: [],
      },
    ],
    current_decisions: [
      {
        statement: "Omit LCD screen to reduce cost.",
        meeting_id: "TS3012c",
        quote: "if we take out the LCD screen we can save fifteen Euros",
        speaker_label: "Speaker C",
        speaker_role: "User Interface",
        status: "CURRENT",
        turn_id: "turn-123",
      },
    ],
    decision_changes: [
      {
        previous_decision: "Include double LCD display",
        updated_decision: "Omit LCD screen to reduce cost",
        previous_meeting_id: "TS3012b",
        updated_meeting_id: "TS3012c",
        previous_quote: "we should definitely have an LCD screen on the front",
        updated_quote: "if we take out the LCD screen we can save fifteen Euros",
        reason: "Cost budget reduction",
        turn_id_previous: "prev-turn",
        turn_id_updated: "curr-turn",
      },
    ],
  },
  validation_status: "PASSED",
  validation_errors: [],
  citations_count: 2,
  meetings_covered: ["TS3012a", "TS3012b", "TS3012c"],
  generation_metadata: {},
  created_at: new Date().toISOString(),
};

describe("DecisionTimelinePage", () => {
  it("renders chronological decision evolution and supersessions", async () => {
    vi.mocked(api.fetchLatestBriefing).mockResolvedValue(mockTimelineBriefing as any);

    render(<DecisionTimelinePage />);

    expect(screen.getByRole("heading", { name: "Decision Evolution Timeline", level: 1 })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Decision Changes & Supersessions/i)).toBeInTheDocument();
      expect(screen.getByText(/Chronological Meeting Sequence/i)).toBeInTheDocument();
      expect(screen.getAllByText("TS3012a").length).toBeGreaterThan(0);
      expect(screen.getAllByText("TS3012b").length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Omit LCD screen to reduce cost/i).length).toBeGreaterThan(0);
    });
  });
});
