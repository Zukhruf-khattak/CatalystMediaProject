import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  Sparkles,
  Send,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Quote,
  Eye,
  ChevronDown,
  ChevronUp,
  Radio,
  BookOpen,
} from "lucide-react";
import { runAgentQuery, streamAgentQuery } from "../lib/api";
import { AgentQueryResponse, AgentStageEvent, AgentCitationItem } from "../types/agent";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { CitationContextModal } from "../components/CitationContextModal";

const BENCHMARK_QUESTIONS = [
  {
    id: "Q01",
    team: "TS3006",
    text: "Why did Team TS3006 decide against fruit and vegetable shapes for the remote?",
  },
  {
    id: "Q02",
    team: "TS3006",
    text: "What material did Team TS3006 choose for the remote body casing?",
  },
  {
    id: "Q03",
    team: "TS3006",
    text: "What corporate colour scheme did Team TS3006 adopt for the product design?",
  },
  {
    id: "Q07",
    team: "TS3012",
    text: "What component did Team TS3012 decide to eliminate in order to reduce production costs?",
  },
  {
    id: "Q11",
    team: "TS3011",
    text: "What battery type did Team TS3011 choose for the remote control?",
  },
];

const STAGES = [
  { key: "input_validation", label: "Input Validation" },
  { key: "query_analysis", label: "Query Analysis" },
  { key: "retrieval_planning", label: "Retrieval Planning" },
  { key: "tool_execution", label: "Tool Execution" },
  { key: "evidence_assessment", label: "Evidence Assessment" },
  { key: "answer_generation", label: "Answer Generation" },
  { key: "citation_validation", label: "Citation Validation" },
  { key: "final_response", label: "Final Response" },
];

const querySchema = z.object({
  question: z.string().min(5, "Question must be at least 5 characters long"),
  team_code: z.string().optional(),
  streaming: z.boolean().default(true),
});

type QueryFormData = z.infer<typeof querySchema>;

export function ResearchAssistantPage() {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<AgentQueryResponse | null>(null);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [stageEvents, setStageEvents] = useState<AgentStageEvent[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<AgentCitationItem | null>(null);
  const [showEvidenceTurns, setShowEvidenceTurns] = useState<boolean>(false);
  const [showEvidenceMemories, setShowEvidenceMemories] = useState<boolean>(false);

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<QueryFormData>({
    defaultValues: {
      question: "",
      team_code: "",
      streaming: true,
    },
  });


  const onSubmit = async (data: QueryFormData) => {
    setLoading(true);
    setError(null);
    setResponse(null);
    setCurrentStage(null);
    setStageEvents([]);

    const payload = {
      question: data.question.trim(),
      team_code: data.team_code ? data.team_code : null,
      max_iterations: 2,
    };

    if (data.streaming) {
      try {
        await streamAgentQuery(
          payload,
          (stageEvent) => {
            setCurrentStage(stageEvent.stage);
            setStageEvents((prev) => [...prev, stageEvent]);
          },
          (finalResponse) => {
            setResponse(finalResponse);
            setLoading(false);
          },
          (err) => {
            setError(err.message || "Streaming query failed");
            setLoading(false);
          }
        );
      } catch (err: any) {
        setError(err.message || "Agent execution failed");
        setLoading(false);
      }
    } else {
      try {
        const res = await runAgentQuery(payload);
        setResponse(res);
      } catch (err: any) {
        setError(err.message || "Agent query failed");
      } finally {
        setLoading(false);
      }
    }
  };

  const handleBenchmarkSelect = (b: typeof BENCHMARK_QUESTIONS[0]) => {
    setValue("question", b.text);
    setValue("team_code", b.team);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
          <Sparkles className="h-3.5 w-3.5" /> LangGraph Autonomous Research Agent
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Question Research Assistant
        </h1>
        <p className="text-slate-400 text-sm max-w-3xl leading-relaxed">
          Ask complex cross-meeting questions about team decisions, component evolutions, and disagreements.
          The stateful LangGraph agent performs hybrid retrieval, examines temporal memory, and synthesizes
          deterministic 1–3 sentence answers with verbatim citations.
        </p>
      </div>

      {/* Benchmark Question Quick-Select */}
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <BookOpen className="h-3.5 w-3.5" /> Curated Benchmark Questions
        </label>
        <div className="flex flex-wrap gap-2">
          {BENCHMARK_QUESTIONS.map((b) => (
            <button
              key={b.id}
              type="button"
              onClick={() => handleBenchmarkSelect(b)}
              className="text-xs rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-left text-slate-300 hover:border-indigo-500/50 hover:bg-slate-800 hover:text-white transition-all flex items-center gap-2"
            >
              <span className="font-mono font-semibold text-indigo-400">{b.id}</span>
              <span className="font-mono text-[10px] text-slate-400 border border-slate-800 rounded px-1">
                {b.team}
              </span>
              <span className="truncate max-w-xs">{b.text}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Query Submission Form */}
      <Card className="border-slate-800">
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="question" className="text-xs font-semibold text-slate-300">
                Research Question
              </label>
              <textarea
                id="question"
                rows={3}
                placeholder="Ask about team decisions, product shapes, material choices, or meeting disagreements..."
                {...register("question")}
                className="w-full rounded-lg border border-slate-800 bg-slate-950/80 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              {errors.question && (
                <p className="text-xs text-rose-400">{errors.question.message}</p>
              )}
            </div>

            <div className="flex flex-wrap items-center justify-between gap-4 pt-1 border-t border-slate-800/80">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <label htmlFor="team_code" className="text-xs text-slate-400">
                    Team:
                  </label>
                  <select
                    id="team_code"
                    {...register("team_code")}
                    className="rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="">All Teams (Auto-Detect)</option>
                    <option value="TS3006">TS3006</option>
                    <option value="TS3012">TS3012</option>
                    <option value="TS3011">TS3011</option>
                    <option value="TS3009">TS3009</option>
                    <option value="ES2003">ES2003</option>
                  </select>
                </div>

                <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-400">
                  <input
                    type="checkbox"
                    {...register("streaming")}
                    className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5"
                  />
                  <span>Stream SSE Execution Stages</span>
                </label>
              </div>

              <Button type="submit" disabled={loading} className="gap-2">
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Executing Graph...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    <span>Run Research Agent</span>
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Real-time Streaming Stepper / Execution Progress */}
      {(loading || stageEvents.length > 0) && (
        <Card className="border-slate-800 bg-slate-950/40">
          <CardHeader className="py-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Radio className={`h-4 w-4 ${loading ? "text-amber-400 animate-pulse" : "text-emerald-400"}`} />
                LangGraph State Machine Execution Flow
              </CardTitle>
              {loading && (
                <span className="text-xs font-mono text-amber-400 flex items-center gap-1.5">
                  <Loader2 className="h-3 w-3 animate-spin" /> Live Stage: {currentStage}
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2">
              {STAGES.map((s, idx) => {
                const event = stageEvents.find((e) => e.stage === s.key);
                const isExecuted = Boolean(event);
                const isCurrent = currentStage === s.key && loading;

                return (
                  <div
                    key={s.key}
                    className={`rounded-lg border p-2 text-center text-xs space-y-1 transition-all ${
                      isCurrent
                        ? "border-amber-500 bg-amber-500/10 text-amber-300 ring-1 ring-amber-500"
                        : isExecuted
                        ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-300"
                        : "border-slate-800/80 bg-slate-900/40 text-slate-400"
                    }`}
                  >
                    <div className="font-mono text-[10px] text-slate-400">0{idx + 1}</div>
                    <div className="font-medium text-[11px] truncate">{s.label}</div>
                    <div className="text-[10px]">
                      {isCurrent ? (
                        <span className="text-amber-400 animate-pulse">Running...</span>
                      ) : isExecuted ? (
                        <span className="text-emerald-400 flex items-center justify-center gap-0.5">
                          <CheckCircle2 className="h-3 w-3" /> Done
                        </span>
                      ) : (
                        <span className="text-slate-400">Waiting</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Callout */}
      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300 flex items-start gap-3">
          <XCircle className="h-5 w-5 shrink-0 text-rose-400 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-rose-200">Agent Query Failed</p>
            <p className="text-rose-300 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Agent Response Card */}
      {response && (
        <Card className="border-slate-800 space-y-6">
          <CardHeader className="border-b border-slate-800/80 pb-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-1">
                <span className="font-mono text-xs text-indigo-400">
                  {response.team_code ? `Team ${response.team_code}` : "Cross-Meeting Synthesis"}
                </span>
                <CardTitle className="text-base text-white">Synthesized Research Answer</CardTitle>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  variant={response.validation_status === "PASSED" ? "success" : "destructive"}
                >
                  Validation: {response.validation_status}
                </Badge>
                <span className="font-mono text-xs text-slate-400">
                  {response.iteration_count} loop iteration{response.iteration_count > 1 ? "s" : ""}
                </span>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Plain Sentence Answer Box */}
            <div className="rounded-xl border border-indigo-500/20 bg-indigo-950/10 p-5 space-y-3">
              <p className="text-base font-normal text-slate-100 leading-relaxed">
                {response.answer}
              </p>

              {/* Supporting Meetings Chips */}
              {response.supporting_meetings && response.supporting_meetings.length > 0 && (
                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-indigo-500/10">
                  <span className="text-xs font-semibold text-slate-400">Corpus Evidence:</span>
                  {response.supporting_meetings.map((m) => (
                    <span
                      key={m}
                      className="font-mono text-xs font-medium text-indigo-300 border border-indigo-500/30 rounded px-2 py-0.5 bg-indigo-900/30"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Insufficient Reason Callout */}
            {!response.is_sufficient && response.insufficient_reason && (
              <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-4 text-xs text-amber-300 flex items-start gap-2.5">
                <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
                <div>
                  <span className="font-semibold">Insufficient Evidence Note:</span>
                  <p className="mt-0.5 text-amber-200">{response.insufficient_reason}</p>
                </div>
              </div>
            )}

            {/* Validation Errors Callout */}
            {response.validation_errors && response.validation_errors.length > 0 && (
              <div className="rounded-lg border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300 space-y-1">
                <span className="font-semibold text-rose-200">Validation Checks:</span>
                <ul className="list-disc pl-4 space-y-0.5 text-rose-300">
                  {response.validation_errors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Citations Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Quote className="h-3.5 w-3.5 text-indigo-400" />
                  Verbatim Transcript Citations ({response.citations.length})
                </h3>
                <span className="text-xs text-slate-400">Click to view surrounding speaker turns</span>
              </div>

              <div className="space-y-2.5">
                {response.citations.map((cite, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-slate-800 bg-slate-950/40 p-4 space-y-2 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-semibold text-indigo-400">
                          {cite.meeting_id}
                        </span>
                        <span className="text-slate-600">·</span>
                        <span className="text-slate-300 font-medium">
                          {cite.speaker_label || "Speaker"}
                        </span>
                        {cite.speaker_role && (
                          <span className="text-slate-400">({cite.speaker_role})</span>
                        )}
                      </div>
                      {cite.turn_id && (
                        <button
                          type="button"
                          onClick={() => setSelectedCitation(cite)}
                          className="flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 bg-indigo-950/40 border border-indigo-500/30 rounded px-2.5 py-1 transition-colors"
                        >
                          <Eye className="h-3 w-3" />
                          <span>Inspect Turn Context</span>
                        </button>
                      )}
                    </div>
                    <p className="text-sm italic text-slate-200 font-serif leading-relaxed">
                      "{cite.quote}"
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Collapsible Supporting Details */}
            <div className="pt-2 border-t border-slate-800/80 space-y-3">
              {/* Transcript Turns Toggle */}
              <div>
                <button
                  type="button"
                  onClick={() => setShowEvidenceTurns(!showEvidenceTurns)}
                  className="flex items-center justify-between w-full text-xs text-slate-400 hover:text-slate-200 py-1"
                >
                  <span>Supporting Transcript Segments ({response.supporting_turns?.length || 0})</span>
                  {showEvidenceTurns ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
                {showEvidenceTurns && (
                  <div className="mt-2 space-y-2">
                    {response.supporting_turns?.map((t, idx) => (
                      <div key={idx} className="rounded-lg border border-slate-800/60 bg-slate-950/30 p-3 text-xs space-y-1">
                        <div className="flex items-center justify-between text-slate-400 font-mono text-[11px]">
                          <span>{t.meeting_code} · {t.speaker_label} (#{t.turn_index})</span>
                          <span>Score: {t.score.toFixed(4)} ({t.retrieval_method})</span>
                        </div>
                        <p className="text-slate-300">{t.raw_text}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Temporal Memories Toggle */}
              <div>
                <button
                  type="button"
                  onClick={() => setShowEvidenceMemories(!showEvidenceMemories)}
                  className="flex items-center justify-between w-full text-xs text-slate-400 hover:text-slate-200 py-1"
                >
                  <span>Supporting Temporal Memories ({response.supporting_memories?.length || 0})</span>
                  {showEvidenceMemories ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
                {showEvidenceMemories && (
                  <div className="mt-2 space-y-2">
                    {response.supporting_memories?.map((m, idx) => (
                      <div key={idx} className="rounded-lg border border-slate-800/60 bg-slate-950/30 p-3 text-xs space-y-1">
                        <div className="flex items-center justify-between text-slate-400 text-[11px]">
                          <span className="font-mono font-semibold text-indigo-400">{m.meeting_code}</span>
                          <span className="uppercase text-slate-400">{m.memory_type} · {m.status}</span>
                        </div>
                        <p className="text-slate-200 font-medium">{m.statement}</p>
                        <p className="text-slate-400 italic">"{m.quote}"</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Interactive Turn Context Modal */}
      {selectedCitation && (
        <CitationContextModal
          turnId={selectedCitation.turn_id || null}
          quote={selectedCitation.quote}
          meetingId={selectedCitation.meeting_id}
          speakerLabel={selectedCitation.speaker_label}
          speakerRole={selectedCitation.speaker_role}
          onClose={() => setSelectedCitation(null)}
        />
      )}
    </div>
  );
}
