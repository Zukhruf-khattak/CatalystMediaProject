import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { CitationContextModal } from "../components/CitationContextModal";
import * as api from "../lib/api";

vi.mock("../lib/api", () => ({
  fetchTurnContext: vi.fn(),
}));

const mockTurnContext = {
  turn: {
    id: "target-turn-id",
    turn_index: 42,
    meeting_id: "TS3006b",
    speaker_label: "Speaker B",
    speaker_role: "Industrial Designer",
    start_time: "00:14:22",
    raw_text: "like a rubber spongy kind of material because it's comfortable to hold",
    is_target: true,
  },
  context: [
    {
      id: "turn-prev",
      turn_index: 41,
      meeting_id: "TS3006b",
      speaker_label: "Speaker A",
      speaker_role: "Project Manager",
      start_time: "00:14:10",
      raw_text: "What about the outer case texture?",
      is_target: false,
    },
    {
      id: "target-turn-id",
      turn_index: 42,
      meeting_id: "TS3006b",
      speaker_label: "Speaker B",
      speaker_role: "Industrial Designer",
      start_time: "00:14:22",
      raw_text: "like a rubber spongy kind of material because it's comfortable to hold",
      is_target: true,
    },
    {
      id: "turn-next",
      turn_index: 43,
      meeting_id: "TS3006b",
      speaker_label: "Speaker D",
      speaker_role: "Marketing",
      start_time: "00:14:35",
      raw_text: "Yes that will appeal to the younger demographic.",
      is_target: false,
    },
  ],
};

describe("CitationContextModal", () => {
  it("renders turn context with preceding, target, and succeeding turns", async () => {
    vi.mocked(api.fetchTurnContext).mockResolvedValueOnce(mockTurnContext as any);
    const onClose = vi.fn();

    render(
      <CitationContextModal
        turnId="target-turn-id"
        quote="like a rubber spongy kind of material"
        meetingId="TS3006b"
        speakerLabel="Speaker B"
        speakerRole="Industrial Designer"
        onClose={onClose}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Verbatim Transcript Context Verification")).toBeInTheDocument();
      expect(screen.getByText(/What about the outer case texture/i)).toBeInTheDocument();
      expect(screen.getByText(/Target Cited Turn #42/i)).toBeInTheDocument();
      expect(screen.getByText(/Yes that will appeal to the younger demographic/i)).toBeInTheDocument();
    });

    const closeBtn = screen.getByRole("button", { name: "Close" });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });
});

