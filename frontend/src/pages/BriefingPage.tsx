import { useState, useEffect } from "react";
import {
  FileText,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  User,
  Eye,
  Copy,
  Check,
  Loader2,
  Calendar,
  AlertCircle,
} from "lucide-react";
import { fetchTS3012Briefing, fetchBriefingVersions } from "../lib/api";
import { BriefingResponse, BriefingCitation } from "../types/briefing";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { CitationContextModal } from "../components/CitationContextModal";

export function BriefingPage() {
  const [briefing, setBriefing] = useState<BriefingResponse | null>(null);
  const [versions, setVersions] = useState<BriefingResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [regenerating, setRegenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"structured" | "markdown">("structured");
  const [copied, setCopied] = useState<boolean>(false);

  // Modal context inspection
  const [inspectCitation, setInspectCitation] = useState<BriefingCitation | null>(null);

  const loadBriefing = async (regenerate = false) => {
    if (regenerate) setRegenerating(true);
    else setLoading(true);
    setError(null);

    try {
      const data = await fetchTS3012Briefing(regenerate);
      setBriefing(data);

      const vList = await fetchBriefingVersions("TS3012");
      setVersions(vList.briefings);
    } catch (err: any) {
      setError(err.message || "Failed to load TS3012 pre-meeting briefing");
    } finally {
      setLoading(false);
      setRegenerating(false);
    }
  };

  useEffect(() => {
    loadBriefing(false);
  }, []);

  const handleCopyMarkdown = () => {
    if (!briefing) return;
    navigator.clipboard.writeText(briefing.content_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const payload = briefing?.structured_payload || {};
  const currentDecisions = payload.current_decisions || [];
  const decisionChanges = payload.decision_changes || [];
  const openActions = payload.open_actions || [];
  const disagreements = payload.unresolved_disagreements || [];
  const requirements = payload.confirmed_requirements || [];
  const keyEntities = payload.key_entities || {};

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
            <FileText className="h-3.5 w-3.5" /> Team TS3012 Executive Intelligence
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Pre-Meeting Briefing · Team TS3012
          </h1>
          <p className="text-slate-400 text-sm max-w-3xl leading-relaxed">
            Autonomous multi-meeting synthesis preparing executives for upcoming meeting TS3012d.
            Every decision, supersession, open action, and disagreement is backed by verified citations.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Version Selector */}
          {versions.length > 1 && (
            <select
              value={briefing?.id}
              onChange={(e) => {
                const selected = versions.find((v) => v.id === e.target.value);
                if (selected) setBriefing(selected);
              }}
              className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  Version v{v.version} ({new Date(v.created_at).toLocaleDateString()})
                </option>
              ))}
            </select>
          )}

          <Button
            onClick={() => loadBriefing(true)}
            disabled={regenerating || loading}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${regenerating ? "animate-spin" : ""}`} />
            <span>{regenerating ? "Regenerating..." : "Regenerate Briefing"}</span>
          </Button>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="py-24 flex flex-col items-center justify-center gap-3 text-slate-400">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
          <span className="text-sm">Synthesizing verified pre-meeting briefing for Team TS3012...</span>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-400 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-rose-200">Failed to load briefing</p>
            <p className="text-rose-300 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && briefing && (
        <div className="space-y-6">
          {/* Metadata Banner */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3 text-xs">
              <Badge variant="success" className="gap-1.5">
                <CheckCircle2 className="h-3 w-3" /> Validation: {briefing.validation_status}
              </Badge>
              <span className="text-slate-600">|</span>
              <span className="font-mono text-slate-300">
                Target: <span className="text-indigo-400 font-semibold">{briefing.target_meeting_code || "TS3012d"}</span>
              </span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-300">
                Version: <span className="font-mono font-semibold">v{briefing.version}</span>
              </span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-300">
                Citations: <span className="font-mono font-semibold text-emerald-400">{briefing.citations_count}</span>
              </span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-400 flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {new Date(briefing.created_at).toLocaleString()}
              </span>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setViewMode("structured")}
                className={`rounded-lg px-3 py-1 text-xs font-medium transition-colors ${
                  viewMode === "structured"
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-800 text-slate-300 hover:text-white"
                }`}
              >
                Executive View
              </button>
              <button
                type="button"
                onClick={() => setViewMode("markdown")}
                className={`rounded-lg px-3 py-1 text-xs font-medium transition-colors ${
                  viewMode === "markdown"
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-800 text-slate-300 hover:text-white"
                }`}
              >
                Raw Markdown
              </button>
            </div>
          </div>

          {/* View Mode: Raw Markdown */}
          {viewMode === "markdown" && (
            <Card className="border-slate-800">
              <CardHeader className="py-3 px-5 border-b border-slate-800/80 flex flex-row items-center justify-between">
                <CardTitle className="text-xs uppercase tracking-wider text-slate-400">
                  Full 9-Section Briefing Markdown Document
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopyMarkdown}
                  className="gap-1.5 text-xs"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  <span>{copied ? "Copied!" : "Copy Markdown"}</span>
                </Button>
              </CardHeader>
              <CardContent className="p-6">
                <pre className="font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed overflow-x-auto bg-slate-950 p-4 rounded-lg border border-slate-800">
                  {briefing.content_markdown}
                </pre>
              </CardContent>
            </Card>
          )}

          {/* View Mode: Structured View */}
          {viewMode === "structured" && (
            <div className="space-y-6">
              {/* 1. Executive Summary */}
              {payload.summary && (
                <Card className="border-slate-800">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-semibold text-slate-200">
                      1. Executive Summary
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-300 leading-relaxed font-sans">
                      {payload.summary}
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* 2. Meeting Coverage */}
              <Card className="border-slate-800">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold text-slate-200">
                    2. Meeting Coverage & Chronological History
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {briefing.meetings_covered.map((m) => (
                      <span
                        key={m}
                        className="font-mono text-xs font-semibold text-indigo-300 border border-indigo-500/30 rounded-lg px-3 py-1.5 bg-indigo-950/30"
                      >
                        {m} (Ingested & Analyzed)
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* 3. Current Confirmed Decisions */}
              <Card className="border-slate-800">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      3. Current Confirmed Decisions ({currentDecisions.length})
                    </CardTitle>
                    <span className="text-xs text-slate-400">Click turn button to inspect evidence</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {currentDecisions.map((dec: any, idx: number) => (
                      <div
                        key={idx}
                        className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-4 space-y-2 hover:border-slate-700 transition-colors"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-semibold text-indigo-400">{dec.meeting_id}</span>
                            <span className="text-slate-600">·</span>
                            <span className="text-slate-300">{dec.speaker_label || "Speaker"}</span>
                            {dec.speaker_role && <span className="text-slate-400">({dec.speaker_role})</span>}
                          </div>
                          {dec.turn_id && (
                            <button
                              type="button"
                              onClick={() =>
                                setInspectCitation({
                                  meeting_id: dec.meeting_id,
                                  quote: dec.quote,
                                  speaker_label: dec.speaker_label,
                                  speaker_role: dec.speaker_role,
                                  turn_id: dec.turn_id,
                                })
                              }
                              className="flex items-center gap-1 text-[11px] font-medium text-indigo-400 hover:text-indigo-300"
                            >
                              <Eye className="h-3 w-3" /> Inspect Context
                            </button>
                          )}
                        </div>
                        <p className="text-sm font-semibold text-slate-100">{dec.statement}</p>
                        <p className="text-xs italic text-slate-300 font-serif">"{dec.quote}"</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* 4. Decision Changes & Supersessions */}
              <Card className="border-slate-800">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
                    <Clock className="h-4 w-4 text-amber-400" />
                    4. Decision Changes & Supersessions ({decisionChanges.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {decisionChanges.map((change: any, idx: number) => (
                      <div
                        key={idx}
                        className="rounded-lg border border-slate-800 bg-slate-950/40 p-4 space-y-3"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-amber-400">
                            {change.previous_meeting_id} → {change.updated_meeting_id}
                          </span>
                          {change.reason && (
                            <Badge variant="warning" className="text-[10px]">
                              {change.reason}
                            </Badge>
                          )}
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                          <div className="rounded bg-slate-900/60 p-3 space-y-1">
                            <span className="text-[10px] text-slate-400 uppercase">Previous:</span>
                            <p className="font-medium text-slate-300 line-through opacity-80">
                              {change.previous_decision}
                            </p>
                            <p className="italic text-slate-400 font-serif">"{change.previous_quote}"</p>
                          </div>
                          <div className="rounded bg-emerald-950/20 border border-emerald-500/20 p-3 space-y-1">
                            <span className="text-[10px] text-emerald-400 uppercase font-semibold">Updated:</span>
                            <p className="font-semibold text-emerald-200">{change.updated_decision}</p>
                            <p className="italic text-slate-200 font-serif">"{change.updated_quote}"</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* 5. Open Actions & Commitments */}
              <Card className="border-slate-800">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
                    <User className="h-4 w-4 text-indigo-400" />
                    5. Open Actions & Commitments ({openActions.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {openActions.map((act: any, idx: number) => (
                      <div
                        key={idx}
                        className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-4 space-y-2 flex flex-col justify-between"
                      >
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-mono text-indigo-400 font-semibold">
                              {act.source_meeting_id}
                            </span>
                            <Badge
                              variant={act.owner_confidence === "EXPLICIT" ? "default" : "outline"}
                              className="text-[10px]"
                            >
                              Owner: {act.owner}
                            </Badge>
                          </div>
                          <p className="text-sm font-medium text-slate-200">{act.description}</p>
                        </div>
                        <div className="rounded bg-slate-900/60 p-2.5 text-xs italic text-slate-400 font-serif">
                          "{act.quote}"
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* 6. Unresolved Disagreements */}
              <Card className="border-slate-800">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-rose-400" />
                    6. Unresolved Disagreements & Points of Friction ({disagreements.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {disagreements.map((dis: any, idx: number) => (
                      <div
                        key={idx}
                        className="rounded-lg border border-rose-500/20 bg-rose-950/10 p-4 space-y-2"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-rose-300">{dis.disputed_issue}</span>
                          <Badge variant="destructive" className="text-[10px]">
                            {dis.resolution_status || "UNRESOLVED"}
                          </Badge>
                        </div>
                        {dis.speakers_involved && dis.speakers_involved.length > 0 && (
                          <div className="text-xs text-slate-400">
                            Speakers Involved: <span className="text-slate-200">{dis.speakers_involved.join(", ")}</span>
                          </div>
                        )}
                        {dis.positions && dis.positions.length > 0 && (
                          <div className="space-y-1">
                            <span className="text-[10px] uppercase tracking-wider text-slate-400">Positions Expressed:</span>
                            <ul className="list-disc pl-4 text-xs text-slate-300 space-y-0.5">
                              {dis.positions.map((p: string, pidx: number) => (
                                <li key={pidx}>{p}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* 7. Product Requirements & 8. Key Entities */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Requirements */}
                <Card className="border-slate-800">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-semibold text-white">
                      7. Confirmed Product Requirements ({requirements.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 text-xs text-slate-300">
                      {requirements.map((req: any, idx: number) => (
                        <li key={idx} className="rounded bg-slate-950/50 p-2.5 border border-slate-800 space-y-1">
                          <div className="flex items-center justify-between font-mono text-[10px] text-indigo-400">
                            <span>Requirement #{idx + 1}</span>
                            <span>{req.meeting_id}</span>
                          </div>
                          <p className="font-medium text-slate-200">{req.requirement}</p>
                          <p className="italic text-slate-400 font-serif">"{req.quote}"</p>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                {/* Key Entities */}
                <Card className="border-slate-800">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-semibold text-white">
                      8. Key Entities & Specifications
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-xs">
                      {Object.entries(keyEntities).map(([key, val]) => (
                        <div
                          key={key}
                          className="flex items-center justify-between rounded bg-slate-950/50 p-2.5 border border-slate-800"
                        >
                          <span className="font-mono text-slate-400">{key}:</span>
                          <span className="font-medium text-slate-200">{String(val)}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modal Inspector */}
      {inspectCitation && (
        <CitationContextModal
          turnId={inspectCitation.turn_id || null}
          quote={inspectCitation.quote}
          meetingId={inspectCitation.meeting_id}
          speakerLabel={inspectCitation.speaker_label}
          speakerRole={inspectCitation.speaker_role}
          onClose={() => setInspectCitation(null)}
        />
      )}
    </div>
  );
}
