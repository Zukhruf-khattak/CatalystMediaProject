import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { BriefingPage } from "../pages/BriefingPage";
import * as api from "../lib/api";

vi.mock("../lib/api", () => ({
  fetchTS3012Briefing: vi.fn(),
  fetchBriefingVersions: vi.fn(),
  fetchTurnContext: vi.fn(),
}));

const mockBriefing = {
  id: "briefing-123",
  team_code: "TS3012",
  target_meeting_code: "TS3012d",
  version: 1,
  title: "Team TS3012 Pre-Meeting Briefing",
  content_markdown: "# Pre-Meeting Briefing: Team TS3012\n\nExecutive briefing content.",
  structured_payload: {
    summary: "Team TS3012 has progressed through three meetings with key decisions on design and cost reduction.",
    current_decisions: [
      {
        statement: "The remote control will omit the LCD display to reduce cost.",
        meeting_id: "TS3012c",
        quote: "if we take out the LCD screen we can save fifteen Euros",
        speaker_label: "Speaker C",
        speaker_role: "User Interface",
        status: "CURRENT",
        turn_id: "turn-abc",
      },
    ],
    decision_changes: [
      {
        previous_decision: "Remote includes double LCD display.",
        updated_decision: "LCD screen removed entirely.",
        previous_meeting_id: "TS3012b",
        updated_meeting_id: "TS3012c",
        previous_quote: "we should definitely have an LCD screen on the front",
        updated_quote: "if we take out the LCD screen we can save fifteen Euros",
        reason: "Cost budget reduction",
        turn_id_previous: "turn-prev",
        turn_id_updated: "turn-curr",
      },
    ],
    open_actions: [
      {
        description: "Prepare foam mock-up for final presentation",
        owner: "Speaker B",
        owner_confidence: "EXPLICIT",
        source_meeting_id: "TS3012c",
        status: "OPEN",
        quote: "I will carve the foam mock-up by tomorrow morning",
        turn_id: "turn-action",
      },
    ],
    unresolved_disagreements: [
      {
        disputed_issue: "Final battery type selection",
        positions: ["AA alkaline batteries", "Rechargeable lithium battery"],
        speakers_involved: ["Speaker B", "Speaker D"],
        resolution_status: "UNRESOLVED",
        citations: [],
      },
    ],
    confirmed_requirements: [
      {
        requirement: "Remote production budget under 25 Euros",
        meeting_id: "TS3012a",
        quote: "our maximum production cost target is twenty five Euros",
      },
    ],
    key_entities: {
      "Target Cost": "25 EUR",
      "Casing Material": "Plastic / Rubber",
    },
  },
  validation_status: "PASSED",
  validation_errors: [],
  citations_count: 5,
  meetings_covered: ["TS3012a", "TS3012b", "TS3012c"],
  generation_metadata: {},
  created_at: new Date().toISOString(),
};

describe("BriefingPage", () => {
  it("renders TS3012 briefing with structured sections and decisions", async () => {
    vi.mocked(api.fetchTS3012Briefing).mockResolvedValueOnce(mockBriefing as any);
    vi.mocked(api.fetchBriefingVersions).mockResolvedValueOnce({ briefings: [mockBriefing as any], total: 1 });

    render(
      <BrowserRouter>
        <BriefingPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Pre-Meeting Briefing · Team TS3012")).toBeInTheDocument();
      expect(screen.getByText(/Validation: PASSED/i)).toBeInTheDocument();
      expect(screen.getByText(/1. Executive Summary/i)).toBeInTheDocument();
      expect(screen.getByText(/The remote control will omit the LCD display to reduce cost/i)).toBeInTheDocument();
      expect(screen.getByText(/4. Decision Changes & Supersessions/i)).toBeInTheDocument();
    });
  });
});
