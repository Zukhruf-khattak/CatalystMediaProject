import { Link } from "react-router-dom";
import {
  Database,
  BrainCircuit,
  Search,
  ShieldCheck,
  FileText,
  ArrowRight,
  Sparkles,
  Quote,
  Layers,
  GitBranch,
  BarChart3,
} from "lucide-react";
import { SystemStatusPanel } from "../features/status/SystemStatusPanel";
import { PhaseTrackerCard } from "../features/status/PhaseTrackerCard";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card";

const WORKFLOW_STEPS = [
  {
    step: "01",
    title: "Ingest Meetings",
    description: "Parse raw transcripts into immutable, verbatim speaker turns with timestamps and speaker identifiers.",
    icon: Database,
  },
  {
    step: "02",
    title: "Build Memory",
    description: "Extract temporal decisions, track changes across sequential meetings (a -> d), and log action owners.",
    icon: BrainCircuit,
  },
  {
    step: "03",
    title: "Research Questions",
    description: "Execute multi-step hybrid retrieval (PostgreSQL FTS + pgvector) driven by a stateful LangGraph agent loop.",
    icon: Search,
  },
  {
    step: "04",
    title: "Validate Evidence",
    description: "Deterministically check every candidate quotation against source transcripts word-for-word within one turn.",
    icon: ShieldCheck,
  },
  {
    step: "05",
    title: "Generate Team Brief",
    description: "Synthesize executive pre-meeting briefs with cited decisions, changes along the way, and open disputes.",
    icon: FileText,
  },
];

const QUICK_ACTIONS = [
  {
    title: "Question Research Assistant",
    description: "Submit multi-meeting queries and stream live LangGraph execution with exact citations.",
    href: "/research",
    icon: Sparkles,
    badge: "Phase 5",
  },
  {
    title: "Citation & Evidence Inspector",
    description: "Inspect verbatim quotations with surrounding ±2 speaker turns and 6-rule validation.",
    href: "/citations",
    icon: Quote,
    badge: "Phase 6",
  },
  {
    title: "Temporal Memory Explorer",
    description: "Query atomic decisions, action owners, and relationship graphs (updates, supersedes).",
    href: "/memory",
    icon: Layers,
    badge: "Phase 3",
  },
  {
    title: "Decision Evolution Timeline",
    description: "View chronological decision morphing and supersessions across sequential meetings.",
    href: "/decisions",
    icon: GitBranch,
    badge: "Phase 3",
  },
  {
    title: "TS3012 Pre-Meeting Briefing",
    description: "View verified 9-section executive intelligence document for upcoming meeting TS3012d.",
    href: "/briefing",
    icon: FileText,
    badge: "Phase 7",
  },
  {
    title: "Evaluation & Benchmarks",
    description: "Inspect measured retrieval metrics (Recall 82%, Precision 90%) and scaling analysis.",
    href: "/evaluation",
    icon: BarChart3,
    badge: "Phase 4 & 6",
  },
];

export function OverviewPage() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
          Catalist Build-Test Foundation · Phase 8 Production UI
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
          Catalist Meeting Intelligence
        </h1>
        <p className="max-w-3xl text-sm md:text-base text-slate-300 leading-relaxed">
          An autonomous intelligence system turning hundreds of hours of raw AMI meeting transcripts
          into a temporally ordered memory store and an automated pre-meeting briefing agent.
          Engineered to scale from 138 transcripts to 10,000+ organizational meetings.
        </p>
      </div>

      {/* Quick Launch Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {QUICK_ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <Link
              key={action.title}
              to={action.href}
              className="group rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3 hover:border-indigo-500/50 hover:bg-slate-900 transition-all flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600/20 text-indigo-400 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="text-[10px] font-semibold text-slate-400 border border-slate-800 rounded px-1.5 py-0.5 bg-slate-950 font-mono">
                    {action.badge}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors">
                  {action.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {action.description}
                </p>
              </div>

              <div className="flex items-center gap-1 text-xs font-medium text-indigo-400 group-hover:translate-x-0.5 transition-transform">
                <span>Launch View</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </div>
            </Link>
          );
        })}
      </div>

      {/* 5-Step Workflow Pipeline */}
      <Card className="border-slate-800">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-white">
            Core Intelligence Workflow
          </CardTitle>
          <CardDescription>
            The five-stage pipeline turning unstructured audio transcripts into cited, verified executive intelligence.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {WORKFLOW_STEPS.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.step}
                  className="relative rounded-lg border border-slate-800/80 bg-slate-950/40 p-4 space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-semibold text-indigo-400">
                        {step.step}
                      </span>
                      <Icon className="h-4 w-4 text-slate-400" />
                    </div>
                    <h3 className="text-sm font-semibold text-slate-200">
                      {step.title}
                    </h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                  {idx < WORKFLOW_STEPS.length - 1 && (
                    <div className="hidden lg:block absolute -right-3.5 top-1/2 -translate-y-1/2 z-10 text-slate-400">
                      <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* System Status Panel */}
      <SystemStatusPanel />

      {/* Phase Tracker Card */}
      <PhaseTrackerCard />
    </div>
  );
}
