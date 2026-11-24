import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { IngestionPage } from "../pages/IngestionPage";
import * as api from "../lib/api";

vi.mock("../lib/api", () => ({
  fetchIngestionStats: vi.fn(),
  fetchIngestionJobs: vi.fn(),
  triggerIngestionJob: vi.fn(),
}));

const mockStats = {
  total_teams: 5,
  total_meetings: 138,
  total_speakers: 20,
  total_turns: 31800,
  embedded_turns: 31800,
  latest_job: null,
};

const mockJobs = {
  jobs: [
    {
      id: "job-001",
      status: "COMPLETED",
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      total_files: 138,
      completed_meetings: 138,
      failed_meetings: 0,
      skipped_meetings: 0,
      total_turns: 31800,
      total_words: 450000,
      embedded_turns: 31800,
      errors_json: [],
      summary_json: {},
    },
  ],
  total_count: 1,
};

describe("IngestionPage", () => {
  it("renders corpus metrics and ingestion job history", async () => {
    vi.mocked(api.fetchIngestionStats).mockResolvedValue(mockStats as any);
    vi.mocked(api.fetchIngestionJobs).mockResolvedValue(mockJobs as any);

    render(<IngestionPage />);

    expect(screen.getByRole("heading", { name: "Meeting Ingestion & Indexing Monitor", level: 1 })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("138")).toBeInTheDocument();
      expect(screen.getAllByText("31,800").length).toBeGreaterThan(0);
      expect(screen.getByText("Ingestion & Parsing Job History")).toBeInTheDocument();
      expect(screen.getByText("COMPLETED")).toBeInTheDocument();
    });
  });
});
