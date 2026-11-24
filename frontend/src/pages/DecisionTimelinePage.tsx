import { useState, useEffect } from "react";
import {
  GitBranch,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  RefreshCw,
  Eye,
} from "lucide-react";
import { fetchLatestBriefing } from "../lib/api";
import { BriefingResponse, DecisionChangeItem, DecisionItem } from "../types/briefing";
import { Card, CardHeader, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { CitationContextModal } from "../components/CitationContextModal";

export function DecisionTimelinePage() {
  const [selectedTeam, setSelectedTeam] = useState<string>("TS3012");
  const [briefing, setBriefing] = useState<BriefingResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modal inspection
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);
  const [selectedQuote, setSelectedQuote] = useState<string | undefined>(undefined);
  const [selectedMeetingId, setSelectedMeetingId] = useState<string | undefined>(undefined);

  const loadTimeline = async (team: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLatestBriefing(team);
      setBriefing(data);
    } catch (err: any) {
      setError(err.message || `Failed to load decision timeline for team ${team}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline(selectedTeam);
  }, [selectedTeam]);

  const timelineMeetings = briefing?.structured_payload?.meetings_timeline || [];
  const currentDecisions = briefing?.structured_payload?.current_decisions || [];
  const decisionChanges = briefing?.structured_payload?.decision_changes || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
            <GitBranch className="h-3.5 w-3.5" /> Sequential Decision Evolution
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Decision Evolution Timeline
          </h1>
          <p className="text-slate-400 text-sm max-w-3xl leading-relaxed">
            Track how decisions morph across sequential project meetings (Meeting a → b → c → d).
            Identify supersessions, cost-driven redesigns, and final confirmed baselines.
          </p>
        </div>

        {/* Team Selector */}
        <div className="flex items-center gap-3">
          <label htmlFor="team-select" className="text-xs text-slate-400">
            Select Team:
          </label>
          <select
            id="team-select"
            value={selectedTeam}
            onChange={(e) => setSelectedTeam(e.target.value)}
            className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none"
          >
            <option value="TS3012">Team TS3012 (Assessment Target)</option>
            <option value="TS3006">Team TS3006 (Ergonomics / Remote)</option>
            <option value="TS3011">Team TS3011 (Battery / Electronics)</option>
            <option value="TS3009">Team TS3009 (Design Concept)</option>
            <option value="ES2003">Team ES2003 (Corporate Identity)</option>
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadTimeline(selectedTeam)}
            disabled={loading}
            className="gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="py-20 flex flex-col items-center justify-center gap-3 text-slate-400">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
          <span className="text-sm">Reconstructing chronological decision evolution for {selectedTeam}...</span>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 shrink-0 text-rose-400 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-rose-200">Unable to load decision timeline</p>
            <p className="text-rose-300 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && briefing && (
        <div className="space-y-8">
          {/* Section 1: Decision Changes (Before -> After Evolution) */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <ArrowRight className="h-4 w-4 text-amber-400" />
                  Decision Changes & Supersessions ({decisionChanges.length})
                </h2>
                <p className="text-xs text-slate-400">
                  Explicit evidence of earlier decisions being overturned or replaced in later meetings.
                </p>
              </div>
            </div>

            {decisionChanges.length === 0 ? (
              <Card className="border-slate-800 p-6 text-center text-xs text-slate-400">
                No decision changes recorded for this team. Decisions remained consistent throughout.
              </Card>
            ) : (
              <div className="space-y-4">
                {decisionChanges.map((change: DecisionChangeItem, idx: number) => (
                  <Card key={idx} className="border-slate-800/80 overflow-hidden">
                    <CardHeader className="bg-slate-950/50 py-3 border-b border-slate-800/80">
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-amber-400">Supersession #{idx + 1}</span>
                          <span className="text-slate-600">·</span>
                          <span className="font-mono text-slate-400">
                            {change.previous_meeting_id} → {change.updated_meeting_id}
                          </span>
                        </div>
                        {change.reason && (
                          <Badge variant="warning" className="text-[10px]">
                            Reason: {change.reason}
                          </Badge>
                        )}
                      </div>
                    </CardHeader>

                    <CardContent className="p-5">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Previous Decision */}
                        <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4 space-y-2">
                          <div className="flex items-center justify-between text-xs text-slate-400">
                            <span className="font-medium text-slate-300">Previous Historical Decision</span>
                            <span className="font-mono text-indigo-400">{change.previous_meeting_id}</span>
                          </div>
                          <p className="text-sm font-medium text-slate-200 line-through opacity-80">
                            {change.previous_decision}
                          </p>
                          <div className="rounded bg-slate-900/80 p-2.5 text-xs italic text-slate-400 font-serif">
                            "{change.previous_quote}"
                          </div>
                          {change.turn_id_previous && (
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedTurnId(change.turn_id_previous || null);
                                setSelectedQuote(change.previous_quote);
                                setSelectedMeetingId(change.previous_meeting_id);
                              }}
                              className="flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300 pt-1"
                            >
                              <Eye className="h-3 w-3" /> Inspect Historical Turn
                            </button>
                          )}
                        </div>

                        {/* Updated Decision */}
                        <div className="rounded-lg border border-emerald-500/30 bg-emerald-950/10 p-4 space-y-2">
                          <div className="flex items-center justify-between text-xs text-emerald-400">
                            <span className="font-medium text-emerald-300">Updated / Superseding Decision</span>
                            <span className="font-mono font-semibold">{change.updated_meeting_id}</span>
                          </div>
                          <p className="text-sm font-semibold text-white">
                            {change.updated_decision}
                          </p>
                          <div className="rounded bg-slate-900/80 p-2.5 text-xs italic text-slate-200 font-serif">
                            "{change.updated_quote}"
                          </div>
                          {change.turn_id_updated && (
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedTurnId(change.turn_id_updated || null);
                                setSelectedQuote(change.updated_quote);
                                setSelectedMeetingId(change.updated_meeting_id);
                              }}
                              className="flex items-center gap-1 text-[11px] text-emerald-400 hover:text-emerald-300 pt-1"
                            >
                              <Eye className="h-3 w-3" /> Inspect Updated Turn
                            </button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Section 2: Chronological Meeting Timeline (a -> b -> c -> d) */}
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Clock className="h-4 w-4 text-indigo-400" />
                Chronological Meeting Sequence
              </h2>
              <p className="text-xs text-slate-400">
                Key topics, decisions, and commitments established in each meeting.
              </p>
            </div>

            <div className="relative pl-6 border-l-2 border-indigo-500/30 space-y-6">
              {timelineMeetings.map((item) => (
                <div key={item.meeting_code} className="relative space-y-3">
                  {/* Timeline Dot */}
                  <div className="absolute -left-[31px] top-1.5 h-4 w-4 rounded-full border-2 border-indigo-400 bg-slate-950 flex items-center justify-center">
                    <div className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
                  </div>

                  {/* Meeting Card */}
                  <Card className="border-slate-800">
                    <CardHeader className="py-3 px-5 border-b border-slate-800/80 bg-slate-950/40">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-indigo-400">
                            {item.meeting_code}
                          </span>
                          <span className="text-slate-600">·</span>
                          <span className="text-xs text-slate-300 font-medium">
                            Meeting #{item.meeting_order} (Sequence {item.sequence_letter.toUpperCase()})
                          </span>
                        </div>
                        <Badge variant="outline" className="text-[10px]">
                          {item.major_decisions.length} Decisions
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="p-5 space-y-4">
                      {/* Discussion Topics */}
                      {item.discussion_topics.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                            Key Discussion Topics:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {item.discussion_topics.map((t, tidx) => (
                              <span
                                key={tidx}
                                className="rounded bg-slate-800/80 px-2 py-0.5 text-xs text-slate-300"
                              >
                                {t}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Major Decisions */}
                      {item.major_decisions.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">
                            Major Decisions Reached:
                          </span>
                          <ul className="list-disc pl-4 space-y-1 text-xs text-slate-200">
                            {item.major_decisions.map((d, didx) => (
                              <li key={didx}>{d}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Significant Changes */}
                      {item.significant_changes.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-400">
                            Changes Relative to Earlier Meetings:
                          </span>
                          <ul className="list-disc pl-4 space-y-1 text-xs text-amber-200/90">
                            {item.significant_changes.map((c, cidx) => (
                              <li key={cidx}>{c}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Current Confirmed Decisions */}
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Latest Confirmed Decisions ({currentDecisions.length})
              </h2>
              <p className="text-xs text-slate-400">
                Active decisions in effect for the upcoming meeting without subsequent overturn.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {currentDecisions.map((dec: DecisionItem, idx: number) => (
                <Card key={idx} className="border-slate-800 flex flex-col justify-between">
                  <CardContent className="p-5 space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-indigo-400 font-semibold">{dec.meeting_id}</span>
                      <Badge variant="success" className="text-[10px]">CURRENT</Badge>
                    </div>
                    <p className="text-sm font-semibold text-slate-100">{dec.statement}</p>
                    <div className="rounded bg-slate-950 p-3 text-xs italic text-slate-300 font-serif border border-slate-800/80">
                      "{dec.quote}"
                    </div>
                    <div className="text-xs text-slate-400">
                      Confirmed by: <span className="text-slate-300">{dec.speaker_label || "Speaker"}</span>
                      {dec.speaker_role && <span> ({dec.speaker_role})</span>}
                    </div>
                  </CardContent>
                  {dec.turn_id && (
                    <div className="border-t border-slate-800/80 bg-slate-950/40 px-5 py-2.5 flex justify-end">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedTurnId(dec.turn_id || null);
                          setSelectedQuote(dec.quote);
                          setSelectedMeetingId(dec.meeting_id);
                        }}
                        className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300"
                      >
                        <Eye className="h-3 w-3" /> Inspect Turn Context
                      </button>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Modal Inspector */}
      {selectedTurnId && (
        <CitationContextModal
          turnId={selectedTurnId}
          quote={selectedQuote}
          meetingId={selectedMeetingId}
          onClose={() => {
            setSelectedTurnId(null);
            setSelectedQuote(undefined);
            setSelectedMeetingId(undefined);
          }}
        />
      )}
    </div>
  );
}
