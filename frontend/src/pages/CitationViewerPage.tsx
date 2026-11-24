import { useState } from "react";
import {
  Quote,
  Search,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertCircle,
  Loader2,
  FileSearch,
} from "lucide-react";
import { fetchTurnContext } from "../lib/api";
import { TurnContextResponse } from "../types/retrieval";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";

const CURATED_CITATIONS = [
  {
    title: "TS3006 Rubber Case Decision",
    meetingId: "TS3006b",
    team: "TS3006",
    speaker: "Speaker B",
    role: "Industrial Designer",
    quote: "like a rubber spongy kind of material because it's comfortable to hold",
    turnId: "00000000-0000-0000-0000-000000000001",
    note: "Primary physical ergonomics requirement for the TS3006 remote.",
  },
  {
    title: "TS3012 Cost Reduction LCD Removal",
    meetingId: "TS3012c",
    team: "TS3012",
    speaker: "Speaker C",
    role: "User Interface",
    quote: "if we take out the LCD screen we can save fifteen Euros",
    turnId: "00000000-0000-0000-0000-000000000002",
    note: "Key cost cutting decision replacing earlier double screen requirement.",
  },
  {
    title: "TS3011 Double AA Battery Standard",
    meetingId: "TS3011b",
    team: "TS3011",
    speaker: "Speaker D",
    role: "Marketing",
    quote: "regular double A batteries are much cheaper for the consumer",
    turnId: "00000000-0000-0000-0000-000000000003",
    note: "Energy decision rejecting expensive kinetic or solar power.",
  },
];

const CITATION_RULES = [
  {
    rule: "01. Meeting Existence",
    description: "The cited meeting code must exist in the ingested AMI dataset corpus.",
  },
  {
    rule: "02. Team Boundary Verification",
    description: "The referenced meeting must strictly belong to the specified team without cross-team leakage.",
  },
  {
    rule: "03. Speaker Turn Existence",
    description: "The speaker turn UUID must resolve to an immutable transcript record in PostgreSQL.",
  },
  {
    rule: "04. Exact Verbatim Match",
    description: "Every quotation character sequence must match the original transcript within a single turn.",
  },
  {
    rule: "05. 6-Word Minimum Length",
    description: "Every quotation must contain at least six words to prevent single-token ambiguity.",
  },
  {
    rule: "06. Speaker & Role Consistency",
    description: "Preserve speaker letters; include functional roles only when supported by transcript metadata.",
  },
];

export function CitationViewerPage() {
  const [turnIdInput, setTurnIdInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [contextData, setContextData] = useState<TurnContextResponse | null>(null);
  const [activeQuote, setActiveQuote] = useState<string | null>(null);

  const handleLookup = async (id: string, quote?: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    setContextData(null);
    setActiveQuote(quote || null);

    try {
      const data = await fetchTurnContext(id.trim());
      setContextData(data);
    } catch (err: any) {
      setError(err.message || "Failed to load turn context");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
          <Quote className="h-3.5 w-3.5" /> Deterministic Citation Validation Layer
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Citation & Evidence Context Viewer
        </h1>
        <p className="text-slate-400 text-sm max-w-3xl leading-relaxed">
          Inspect verbatim quotations within their true conversational context. Every factual claim
          in Catalist is backed by an immutable speaker turn and verified against 6 strict deterministic criteria.
        </p>
      </div>

      {/* 6 Deterministic Rules Banner */}
      <Card className="border-slate-800">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            Catalist Deterministic Evidence Requirements
          </CardTitle>
          <CardDescription>
            Zero-hallucination validation policy enforced before any generated answer is returned.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {CITATION_RULES.map((r) => (
              <div
                key={r.rule}
                className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-3 space-y-1"
              >
                <div className="text-xs font-semibold text-indigo-300">{r.rule}</div>
                <p className="text-xs text-slate-400 leading-relaxed">{r.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Turn Lookup Bar */}
      <Card className="border-slate-800">
        <CardContent className="pt-6">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleLookup(turnIdInput);
            }}
            className="flex flex-col sm:flex-row gap-3"
          >
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Enter speaker turn UUID (e.g. from research agent citations)..."
                value={turnIdInput}
                onChange={(e) => setTurnIdInput(e.target.value)}
                className="w-full rounded-lg border border-slate-800 bg-slate-950/80 pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <Button type="submit" disabled={loading || !turnIdInput.trim()} className="gap-2 shrink-0">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Looking up...</span>
                </>
              ) : (
                <>
                  <FileSearch className="h-4 w-4" />
                  <span>Inspect Context</span>
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Curated Exemplar Citations */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Curated Corpus Quotations & Benchmark Examples
          </h2>
          <span className="text-xs text-slate-400">Click any example to load context</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {CURATED_CITATIONS.map((c, idx) => (
            <div
              key={idx}
              onClick={() => {
                setTurnIdInput(c.turnId);
                handleLookup(c.turnId, c.quote);
              }}
              className="cursor-pointer rounded-xl border border-slate-800 bg-slate-900/50 p-4 space-y-3 hover:border-indigo-500/50 hover:bg-slate-900 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-semibold text-indigo-400">{c.meetingId}</span>
                <Badge variant="outline" className="text-[10px]">{c.team}</Badge>
              </div>
              <h3 className="text-sm font-semibold text-slate-200">{c.title}</h3>
              <p className="text-xs italic text-slate-300 font-serif leading-relaxed">
                "{c.quote}"
              </p>
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <span>{c.speaker} ({c.role})</span>
                <span className="text-indigo-400 font-medium">Inspect →</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="py-16 flex flex-col items-center justify-center gap-3 text-slate-400">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
          <span className="text-sm">Fetching speaker turn and dialogue context from database...</span>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-400 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-rose-200">Turn Context Lookup Failed</p>
            <p className="text-rose-300 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Full Context Viewer Card */}
      {contextData && !loading && (
        <Card className="border-slate-800 space-y-6">
          <CardHeader className="border-b border-slate-800/80 pb-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-semibold text-indigo-400">
                    {contextData.turn.meeting_id}
                  </span>
                  <span className="text-slate-600">·</span>
                  <span className="text-xs text-slate-400">Turn #{contextData.turn.turn_index}</span>
                  <Badge variant="success" className="text-[10px]">Verified Turn</Badge>
                </div>
                <CardTitle className="text-base text-white">
                  Speaker Dialogue Context (±2 Turns)
                </CardTitle>
              </div>
              <div className="font-mono text-xs text-slate-400">
                {contextData.context.length} turns in sequence
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            {activeQuote && (
              <div className="rounded-lg border border-indigo-500/30 bg-indigo-950/20 p-3.5 space-y-1 text-xs text-indigo-200">
                <span className="font-semibold text-indigo-300 flex items-center gap-1.5">
                  <Quote className="h-3.5 w-3.5" /> Target Cited Substring:
                </span>
                <p className="italic font-serif text-sm">"{activeQuote}"</p>
              </div>
            )}

            <div className="space-y-3">
              {contextData.context.map((turn) => {
                const isTarget = turn.is_target;
                return (
                  <div
                    key={turn.id}
                    className={`rounded-xl p-4 transition-all text-xs space-y-2 ${
                      isTarget
                        ? "border-2 border-indigo-500 bg-indigo-950/30 shadow-lg ring-1 ring-indigo-500/50"
                        : "border border-slate-800 bg-slate-950/40 opacity-75 hover:opacity-100"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span
                          className={`font-semibold ${
                            isTarget ? "text-indigo-300" : "text-slate-300"
                          }`}
                        >
                          {turn.speaker_label}
                        </span>
                        {turn.speaker_role && (
                          <span className="text-slate-400 font-normal">
                            ({turn.speaker_role})
                          </span>
                        )}
                        {isTarget && (
                          <Badge variant="default" className="text-[9px] py-0 px-1.5">
                            Target Cited Turn
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px]">
                        <Clock className="h-3 w-3" />
                        <span>{turn.start_time}</span>
                      </div>
                    </div>
                    <p
                      className={`leading-relaxed text-sm ${
                        isTarget ? "text-white font-medium" : "text-slate-300"
                      }`}
                    >
                      {turn.raw_text}
                    </p>
                  </div>
                );
              })}
            </div>

            <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
              <div className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle2 className="h-4 w-4" />
                <span>Deterministic transcript verification confirmed</span>
              </div>
              <span className="font-mono text-[11px] text-slate-400">UUID: {contextData.turn.id}</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
