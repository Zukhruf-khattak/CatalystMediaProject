import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { ResearchAssistantPage } from "../pages/ResearchAssistantPage";
import * as api from "../lib/api";

vi.mock("../lib/api", () => ({
  runAgentQuery: vi.fn(),
  streamAgentQuery: vi.fn(),
  fetchTurnContext: vi.fn(),
}));

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
}

describe("ResearchAssistantPage", () => {
  it("renders page header and question input form", () => {
    renderWithRouter(<ResearchAssistantPage />);
    expect(screen.getByRole("heading", { name: "Question Research Assistant", level: 1 })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask about team decisions/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Run Research Agent/i })).toBeInTheDocument();
  });

  it("renders benchmark question pills and fills the form when clicked", () => {
    renderWithRouter(<ResearchAssistantPage />);
    const q01Pill = screen.getByText("Q01");
    expect(q01Pill).toBeInTheDocument();

    fireEvent.click(q01Pill);
    const textarea = screen.getByPlaceholderText(/Ask about team decisions/i) as HTMLTextAreaElement;
    expect(textarea.value).toContain("Team TS3006");
  });

  it("renders agent response card after successful query submission", async () => {
    vi.mocked(api.runAgentQuery).mockResolvedValueOnce({
      question: "Why did Team TS3006 decide against fruit and vegetable shapes for the remote?",
      answer: "Team TS3006 rejected fruit and vegetable shapes because corporate clients found them unprofessional.",
      is_sufficient: true,
      citations: [
        {
          meeting_id: "TS3006a",
          quote: "fruit and vegetable shapes are too childish for corporate buyers",
          speaker_label: "Speaker B",
          speaker_role: "Industrial Designer",
          turn_id: "11111111-1111-1111-1111-111111111111",
          turn_index: 42,
        },
      ],
      supporting_turns: [],
      supporting_memories: [],
      steps_taken: ["input_validation", "final_response"],
      session_id: "test-session-id",
      iteration_count: 1,
      team_code: "TS3006",
      validation_status: "PASSED",
      validation_errors: [],
      supporting_meetings: ["TS3006a"],
      created_at: new Date().toISOString(),
    });

    renderWithRouter(<ResearchAssistantPage />);

    // Uncheck streaming to use direct runAgentQuery
    const streamCheckbox = screen.getByLabelText(/Stream SSE Execution Stages/i);
    fireEvent.click(streamCheckbox);

    const textarea = screen.getByPlaceholderText(/Ask about team decisions/i);
    fireEvent.change(textarea, {
      target: { value: "Why did Team TS3006 decide against fruit and vegetable shapes for the remote?" },
    });

    const submitBtn = screen.getByRole("button", { name: /Run Research Agent/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Synthesized Research Answer")).toBeInTheDocument();
      expect(screen.getByText(/corporate clients found them unprofessional/i)).toBeInTheDocument();
      expect(screen.getByText(/Validation: PASSED/i)).toBeInTheDocument();
    });
  });
});

