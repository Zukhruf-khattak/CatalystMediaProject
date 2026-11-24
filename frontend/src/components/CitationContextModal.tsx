import { useEffect, useState } from "react";
import { X, CheckCircle2, Clock, User, Quote, AlertCircle, Loader2 } from "lucide-react";
import { fetchTurnContext } from "../lib/api";
import { TurnContextResponse } from "../types/retrieval";
import { Badge } from "./ui/badge";

export interface CitationContextModalProps {
  turnId: string | null;
  quote?: string;
  meetingId?: string;
  speakerLabel?: string | null;
  speakerRole?: string | null;
  onClose: () => void;
}

export function CitationContextModal({
  turnId,
  quote,
  meetingId,
  speakerLabel,
  speakerRole,
  onClose,
}: CitationContextModalProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [contextData, setContextData] = useState<TurnContextResponse | null>(null);

  useEffect(() => {
    if (!turnId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchTurnContext(turnId)
      .then((data) => {
        if (isMounted) {
          setContextData(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to load turn context");
          setLoading(false);
        }
      });

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      isMounted = false;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [turnId, onClose]);

  if (!turnId) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl max-h-[85vh] overflow-hidden rounded-xl border border-slate-700 bg-slate-900 shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/40">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold text-indigo-400">
                {meetingId || contextData?.turn?.meeting_id || "Meeting Evidence"}
              </span>
              <span className="text-slate-600">/</span>
              <span className="text-xs text-slate-400">Turn Context Inspector</span>
              <Badge variant="success" className="text-[10px] ml-2">
                Deterministic Match
              </Badge>
            </div>
            <h3 className="text-sm font-semibold text-white">
              Verbatim Transcript Context Verification
            </h3>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Cited Quotation Box */}
          {quote && (
            <div className="rounded-lg border border-indigo-500/30 bg-indigo-950/20 p-4 space-y-2">
              <div className="flex items-center justify-between text-xs text-indigo-400">
                <span className="flex items-center gap-1.5 font-medium">
                  <Quote className="h-3.5 w-3.5" /> Cited Evidence Quote
                </span>
                <span className="font-mono text-[11px] text-slate-400">
                  {quote.trim().split(/\s+/).length} words
                </span>
              </div>
              <p className="text-sm italic text-indigo-100 font-serif leading-relaxed">
                "{quote}"
              </p>
              <div className="flex items-center gap-3 text-xs text-slate-400 pt-1 border-t border-indigo-500/10">
                {speakerLabel && (
                  <span className="flex items-center gap-1">
                    <User className="h-3 w-3 text-indigo-400" />
                    {speakerLabel}
                  </span>
                )}
                {speakerRole && (
                  <span className="text-slate-400">({speakerRole})</span>
                )}
              </div>
            </div>
          )}

          {/* Context Sequence */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <span>Dialogue Context (±2 Speaker Turns)</span>
              <span className="font-mono text-[11px] text-slate-400">Turn ID: {turnId.slice(0, 8)}...</span>
            </div>

            {loading && (
              <div className="py-12 flex flex-col items-center justify-center gap-3 text-slate-400">
                <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
                <span className="text-xs">Retrieving speaker turn context from corpus...</span>
              </div>
            )}

            {error && (
              <div className="rounded-lg border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
                <div>
                  <p className="font-semibold">Unable to load dialogue context</p>
                  <p className="text-rose-400 mt-0.5">{error}</p>
                </div>
              </div>
            )}

            {contextData && !loading && (
              <div className="space-y-3">
                {contextData.context.map((turn) => {
                  const isTarget = turn.is_target;
                  return (
                    <div
                      key={turn.id}
                      className={`rounded-lg p-3.5 transition-all text-xs space-y-1.5 ${
                        isTarget
                          ? "border-2 border-indigo-500 bg-indigo-950/40 shadow-md ring-1 ring-indigo-500/50"
                          : "border border-slate-800 bg-slate-950/30 opacity-75 hover:opacity-100"
                      }`}
                    >
                      <div className="flex items-center justify-between text-[11px]">
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
                              Target Cited Turn #{turn.turn_index}
                            </Badge>
                          )}
                          {!isTarget && (
                            <span className="text-slate-400 font-mono">#{turn.turn_index}</span>
                          )}
                        </div>
                        <div className="flex items-center gap-1.5 text-slate-400 font-mono">
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
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 bg-slate-950/60 px-6 py-3 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <CheckCircle2 className="h-4 w-4" />
            <span>Exact quote verified against original transcript turn</span>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
