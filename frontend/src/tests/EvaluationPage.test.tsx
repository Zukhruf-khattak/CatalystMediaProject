import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { EvaluationPage } from "../pages/EvaluationPage";

describe("EvaluationPage", () => {
  it("renders measured benchmark metrics and comparison tables", () => {
    render(<EvaluationPage />);

    expect(screen.getByRole("heading", { name: "Evaluation & Empirical Verification", level: 1 })).toBeInTheDocument();
    expect(screen.getAllByText("Recall@10").length).toBeGreaterThan(0);
    expect(screen.getAllByText("82.0%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Precision@10").length).toBeGreaterThan(0);
    expect(screen.getAllByText("90.0%").length).toBeGreaterThan(0);
    expect(screen.getByText("MRR (Mean Reciprocal Rank)")).toBeInTheDocument();
    expect(screen.getByText("0.9000")).toBeInTheDocument();
    expect(screen.getByText(/Hybrid Retrieval Performance vs. Single Modalities/i)).toBeInTheDocument();
    expect(screen.getByText(/Citation Validation Failure Mode Test Suite/i)).toBeInTheDocument();
    expect(screen.getByText(/13 \/ 13 Passing \(100%\)/i)).toBeInTheDocument();
    expect(screen.getByText(/10,000 Meetings Ready/i)).toBeInTheDocument();
  });
});
