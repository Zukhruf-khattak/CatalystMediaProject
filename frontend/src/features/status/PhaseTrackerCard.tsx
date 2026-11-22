import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { CheckCircle2, Clock, PlayCircle } from "lucide-react";
import { PhaseInfo } from "../../types/status";

const PHASES: PhaseInfo[] = [
  {
    id: "01",
    number: "Phase 1",
    title: "Engineering Foundation & Architecture",
    status: "completed",
    description: "Repository baseline, layered FastAPI backend, React shell, Docker Compose, Alembic pgvector, and automated test suite.",
  },
  {
    id: "02",
    number: "Phase 2",
    title: "Dataset Ingestion & Indexing",
    status: "ready",
    description: "Resumable parsing of 138 AMI transcripts into verbatim speaker turns, local embeddings, and FTS lexical indices.",
  },
  {
    id: "03",
    number: "Phase 3",
    title: "Memory System & Temporal Architecture",
    status: "planned",
    description: "Short-term context memory, persistent decision lifecycle tracking, and chronological superseding logic.",
  },
  {
    id: "04",
    number: "Phase 4",
    title: "Hybrid Retrieval Engine",
    status: "planned",
    description: "Reciprocal Rank Fusion (RRF) combining PostgreSQL full-text search with pgvector cosine distance.",
  },
  {
    id: "05",
    number: "Phase 5",
    title: "LangGraph Multi-Step Research Agent",
    status: "planned",
    description: "Stateful research loop with query refinement, bounded context retrieval, and checkpointing.",
  },
  {
    id: "06",
    number: "Phase 6",
    title: "Deterministic Citation Validation",
    status: "planned",
    description: "Word-for-word string verification against source turns with single-turn bounds and >= 6 words rule.",
  },
  {
    id: "07",
    number: "Phase 7",
    title: "Team TS3012 Pre-Meeting Briefing",
    status: "planned",
    description: "Synthesized executive pre-meeting brief covering decisions, changes, open actions, and disagreements.",
  },
  {
    id: "08",
    number: "Phase 8",
    title: "Interactive React UI & Visualizer",
    status: "planned",
    description: "Full research query interface, interactive answer review, and cited briefing reader.",
  },
  {
    id: "09",
    number: "Phase 9",
    title: "Evaluation Benchmark & Submission",
    status: "planned",
    description: "25 assessment questions, 10 author-verified benchmark, 3 failure analyses, and scale estimation.",
  },
];

export function PhaseTrackerCard() {
  return (
    <Card className="border-slate-800">
      <CardHeader>
        <CardTitle className="text-base font-semibold text-white">
          Implementation Roadmap & Phase Tracker
        </CardTitle>
        <CardDescription>
          Static architectural plan showing incremental deliverables. No speculative or faked operational metrics.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {PHASES.map((phase) => (
            <div
              key={phase.id}
              className="flex items-start justify-between rounded-lg border border-slate-800/80 bg-slate-950/40 p-3.5 transition-colors hover:border-slate-700/80"
            >
              <div className="space-y-1 pr-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-indigo-400 font-mono">
                    {phase.number}
                  </span>
                  <span className="text-sm font-medium text-slate-200">
                    {phase.title}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {phase.description}
                </p>
              </div>

              <div className="shrink-0 pt-0.5">
                {phase.status === "completed" && (
                  <Badge variant="success" className="gap-1">
                    <CheckCircle2 className="h-3 w-3" /> Completed
                  </Badge>
                )}
                {phase.status === "ready" && (
                  <Badge variant="default" className="gap-1">
                    <PlayCircle className="h-3 w-3" /> Ready
                  </Badge>
                )}
                {phase.status === "planned" && (
                  <Badge variant="outline" className="gap-1 text-slate-400 border-slate-800">
                    <Clock className="h-3 w-3" /> Planned
                  </Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
