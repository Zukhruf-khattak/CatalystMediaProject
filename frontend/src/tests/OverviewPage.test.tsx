import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { OverviewPage } from "../pages/OverviewPage";

// Mock the API calls so test runs cleanly and deterministically
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

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
}

describe("OverviewPage", () => {
  it("renders the product title and description", () => {
    renderWithClient(<OverviewPage />);
    expect(
      screen.getByRole("heading", { name: "Catalist Meeting Intelligence", level: 1 })
    ).toBeInTheDocument();
  });

  it("renders all 5 steps of the intelligence workflow", () => {
    renderWithClient(<OverviewPage />);
    expect(screen.getByText("Ingest Meetings")).toBeInTheDocument();
    expect(screen.getByText("Build Memory")).toBeInTheDocument();
    expect(screen.getByText("Research Questions")).toBeInTheDocument();
    expect(screen.getByText("Validate Evidence")).toBeInTheDocument();
    expect(screen.getByText("Generate Team Brief")).toBeInTheDocument();
  });

  it("renders the phase implementation tracker with Phase 1", () => {
    renderWithClient(<OverviewPage />);
    expect(screen.getByText("Implementation Roadmap & Phase Tracker")).toBeInTheDocument();
    expect(screen.getByText("Phase 1")).toBeInTheDocument();
    expect(screen.getByText("Phase 2")).toBeInTheDocument();
  });
});

