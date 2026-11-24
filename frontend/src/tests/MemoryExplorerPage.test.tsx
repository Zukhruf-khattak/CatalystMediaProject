import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryExplorerPage } from "../pages/MemoryExplorerPage";
import * as api from "../lib/api";

vi.mock("../lib/api", () => ({
  searchMemories: vi.fn(),
  fetchTurnContext: vi.fn(),
}));

const mockMemoriesResponse = {
  items: [
    {
      id: "mem-1",
      team_id: "team-uuid",
      meeting_id: "meeting-uuid",
      turn_id: "turn-uuid-1",
      memory_type: "DECISION",
      statement: "Selected curved banana shape for ergonomic hold.",
      quote: "a curved shape fits naturally in the user hand",
      speaker_label: "Speaker B",
      speaker_role: "Industrial Designer",
      meeting_order: 2,
      sequence_letter: "b",
      status: "current",
      confidence: 1.0,
      extraction_version: "1.0.0",
      metadata_json: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      outgoing_relationships: [],
      incoming_relationships: [],
    },
  ],
  total_count: 1,
  limit: 50,
  offset: 0,
};

describe("MemoryExplorerPage", () => {
  it("renders search controls and loads memory records", async () => {
    vi.mocked(api.searchMemories).mockResolvedValue(mockMemoriesResponse as any);

    render(<MemoryExplorerPage />);

    expect(screen.getByRole("heading", { name: "Temporal Memory Explorer", level: 1 })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Selected curved banana shape for ergonomic hold.")).toBeInTheDocument();
      expect(screen.getByText(/a curved shape fits naturally in the user hand/i)).toBeInTheDocument();
      expect(screen.getAllByText("DECISION").length).toBeGreaterThan(0);
    });
  });
});
