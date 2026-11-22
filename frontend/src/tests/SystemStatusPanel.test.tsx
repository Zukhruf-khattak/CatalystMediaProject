import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SystemStatusPanel } from "../features/status/SystemStatusPanel";
import * as api from "../lib/api";

vi.mock("../lib/api");

describe("SystemStatusPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders healthy operational state when API and DB respond OK", async () => {
    vi.mocked(api.fetchHealth).mockResolvedValue({
      status: "healthy",
      app_name: "Catalist Meeting Intelligence",
      version: "0.1.0",
      environment: "development",
    });
    vi.mocked(api.fetchReady).mockResolvedValue({
      status: "ready",
      database: true,
      app_name: "Catalist Meeting Intelligence",
      version: "0.1.0",
      environment: "development",
    });

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <SystemStatusPanel />
      </QueryClientProvider>
    );

    expect(await screen.findByText("All Foundation Systems Operational")).toBeInTheDocument();
    expect(screen.getByText("Connected")).toBeInTheDocument();
    expect(screen.getByText("200 OK")).toBeInTheDocument();
  });

  it("renders degraded state when database probe returns false", async () => {
    vi.mocked(api.fetchHealth).mockResolvedValue({
      status: "healthy",
      app_name: "Catalist Meeting Intelligence",
      version: "0.1.0",
      environment: "development",
    });
    vi.mocked(api.fetchReady).mockResolvedValue({
      status: "degraded",
      database: false,
      app_name: "Catalist Meeting Intelligence",
      version: "0.1.0",
      environment: "development",
    });

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <SystemStatusPanel />
      </QueryClientProvider>
    );

    expect(await screen.findByText("Database Degraded")).toBeInTheDocument();
    expect(screen.getByText("503 Timeout")).toBeInTheDocument();
  });

  it("handles backend API connection error gracefully without crashing", async () => {
    vi.mocked(api.fetchHealth).mockRejectedValue(new Error("Network connection refused"));
    vi.mocked(api.fetchReady).mockRejectedValue(new Error("Network connection refused"));

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <SystemStatusPanel />
      </QueryClientProvider>
    );

    expect(await screen.findByText("Backend API Unreachable")).toBeInTheDocument();
    expect(screen.getByText("Offline")).toBeInTheDocument();
  });
});
