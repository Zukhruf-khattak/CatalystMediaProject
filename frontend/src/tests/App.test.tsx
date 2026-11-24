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

  it("renders sidebar navigation links across all intelligence phases", () => {
    render(<App />);
    expect(screen.getByText("Overview & Status")).toBeInTheDocument();
    expect(screen.getByText("Research Assistant")).toBeInTheDocument();
    expect(screen.getByText("Citation Context")).toBeInTheDocument();
    expect(screen.getByText("Memory Explorer")).toBeInTheDocument();
    expect(screen.getByText("Decision Timeline")).toBeInTheDocument();
    expect(screen.getByText("TS3012 Briefing")).toBeInTheDocument();
    expect(screen.getByText("Meeting Ingestion")).toBeInTheDocument();
    expect(screen.getByText("Evaluation Benchmark")).toBeInTheDocument();
  });
});
