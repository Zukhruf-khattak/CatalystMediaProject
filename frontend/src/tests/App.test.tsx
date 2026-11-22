import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { App } from "../app/App";

vi.mock("../lib/api", () => ({
  fetchHealth: vi.fn().mockResolvedValue({
    status: "healthy",
    app_name: "Catalist Meeting Intelligence",
    version: "0.1.0",
    environment: "development",
  }),
  fetchReady: vi.fn().mockResolvedValue({
    status: "ready",
    database: true,
    app_name: "Catalist Meeting Intelligence",
    version: "0.1.0",
    environment: "development",
  }),
}));

describe("App", () => {
  it("renders layout header with product title and status indicator", () => {
    render(<App />);
    expect(screen.getAllByText("Catalist Meeting Intelligence").length).toBeGreaterThan(0);
    expect(screen.getByText("Overview & Status")).toBeInTheDocument();
  });

  it("renders sidebar navigation links with future phase badges", () => {
    render(<App />);
    expect(screen.getByText("Meeting Ingestion")).toBeInTheDocument();
    expect(screen.getAllByText("Phase 2").length).toBeGreaterThan(0);
    expect(screen.getByText("Question Research")).toBeInTheDocument();
    expect(screen.getByText("Team Briefings")).toBeInTheDocument();
    expect(screen.getByText("Evaluation Benchmark")).toBeInTheDocument();
  });
});
