import { useState, useEffect } from "react";
import {
  HardDrive,
  Database,
  Users,
  MessageSquare,
  Sparkles,
  RefreshCw,
  Play,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { fetchIngestionStats, fetchIngestionJobs, triggerIngestionJob } from "../lib/api";
import { IngestionJob, IngestionStatsResponse } from "../types/ingestion";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";

export function IngestionPage() {
  const [stats, setStats] = useState<IngestionStatsResponse | null>(null);
  const [jobs, setJobs] = useState<IngestionJob[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [triggering, setTriggering] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showTriggerModal, setShowTriggerModal] = useState<boolean>(false);

  // Trigger form options
  const [forceReingest, setForceReingest] = useState<boolean>(false);
  const [skipEmbeddings, setSkipEmbeddings] = useState<boolean>(false);
  const [limitFiles, setLimitFiles] = useState<string>("");

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, jobsData] = await Promise.all([
        fetchIngestionStats(),
        fetchIngestionJobs(10),
      ]);
      setStats(statsData);
      setJobs(jobsData.jobs);
    } catch (err: any) {
      setError(err.message || "Failed to load ingestion data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleLaunchJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setTriggering(true);
    try {
      await triggerIngestionJob({
        force_reingest: forceReingest,
        skip_embeddings: skipEmbeddings,
        limit_files: limitFiles ? parseInt(limitFiles, 10) : null,
      });
      setShowTriggerModal(false);
      await loadData();
    } catch (err: any) {
      alert(`Error launching job: ${err.message}`);
    } finally {
      setTriggering(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case "COMPLETED":
        return <Badge variant="success">COMPLETED</Badge>;
      case "RUNNING":
        return <Badge variant="warning">RUNNING</Badge>;
      case "FAILED":
        return <Badge variant="destructive">FAILED</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
            <HardDrive className="h-3.5 w-3.5" /> Phase 2 Ingestion & Corpus Indexing
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Meeting Ingestion & Indexing Monitor
          </h1>
          <p className="text-slate-400 text-sm max-w-3xl leading-relaxed">
            Source-of-truth store indexing the 138 AMI meeting transcripts. Tracks verbatim speaker turns,
            dense CPU embeddings (384d all-MiniLM-L6-v2), and PostgreSQL GIN full-text indexes.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            className="gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>

          <Button
            size="sm"
            onClick={() => setShowTriggerModal(true)}
            className="gap-1.5"
          >
            <Play className="h-3.5 w-3.5" />
            <span>Trigger Ingestion</span>
          </Button>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="py-20 flex flex-col items-center justify-center gap-3 text-slate-400">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
          <span className="text-sm">Fetching ingestion metrics and index telemetry...</span>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-400 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-rose-200">Unable to load ingestion status</p>
            <p className="text-rose-300 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Metrics Cards */}
      {!loading && stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="border-slate-800">
            <CardContent className="p-5 space-y-1.5">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Teams</span>
                <Users className="h-4 w-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-bold text-white">{stats.total_teams}</div>
              <p className="text-[11px] text-slate-400">AMI Design Teams</p>
            </CardContent>
          </Card>

          <Card className="border-slate-800">
            <CardContent className="p-5 space-y-1.5">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Meetings Ingested</span>
                <Database className="h-4 w-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-white">{stats.total_meetings}</div>
              <p className="text-[11px] text-slate-400">Transcripts Stored</p>
            </CardContent>
          </Card>

          <Card className="border-slate-800">
            <CardContent className="p-5 space-y-1.5">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Speaker Turns</span>
                <MessageSquare className="h-4 w-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-white">
                {stats.total_turns.toLocaleString()}
              </div>
              <p className="text-[11px] text-slate-400">Immutable Turns</p>
            </CardContent>
          </Card>

          <Card className="border-slate-800">
            <CardContent className="p-5 space-y-1.5">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Dense Embeddings</span>
                <Sparkles className="h-4 w-4 text-purple-400" />
              </div>
              <div className="text-2xl font-bold text-white">
                {stats.embedded_turns.toLocaleString()}
              </div>
              <p className="text-[11px] text-slate-400">384-dim Vectors</p>
            </CardContent>
          </Card>

          <Card className="border-slate-800">
            <CardContent className="p-5 space-y-1.5">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Total Speakers</span>
                <Users className="h-4 w-4 text-sky-400" />
              </div>
              <div className="text-2xl font-bold text-white">{stats.total_speakers}</div>
              <p className="text-[11px] text-slate-400">Participant Personas</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Ingestion Jobs History Table */}
      {!loading && (
        <Card className="border-slate-800">
          <CardHeader className="py-4 border-b border-slate-800/80">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-semibold text-white">
                  Ingestion & Parsing Job History
                </CardTitle>
                <CardDescription className="text-xs">
                  Audit logs of transcript parsing, validation, and embedding generation jobs.
                </CardDescription>
              </div>
              <span className="font-mono text-xs text-slate-400">{jobs.length} jobs recorded</span>
            </div>
          </CardHeader>
          <CardContent className="p-0 overflow-x-auto">
            {jobs.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                No ingestion jobs found in database.
              </div>
            ) : (
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Job ID</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Started At</th>
                    <th className="px-4 py-3">Files / Meetings</th>
                    <th className="px-4 py-3">Turns Ingested</th>
                    <th className="px-4 py-3">Embedded</th>
                    <th className="px-4 py-3">Errors</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {jobs.map((job) => (
                    <tr key={job.id} className="hover:bg-slate-900/40">
                      <td className="px-4 py-3 font-mono text-[11px] text-indigo-400">
                        {job.id.slice(0, 8)}...
                      </td>
                      <td className="px-4 py-3">{getStatusBadge(job.status)}</td>
                      <td className="px-4 py-3 text-slate-300 font-mono text-[11px]">
                        {new Date(job.started_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-slate-200">
                        {job.completed_meetings} / {job.total_files || job.completed_meetings}
                      </td>
                      <td className="px-4 py-3 text-slate-200 font-mono">
                        {job.total_turns.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-slate-200 font-mono">
                        {job.embedded_turns.toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        {job.errors_json.length > 0 ? (
                          <span className="text-rose-400 font-semibold">
                            {job.errors_json.length} errors
                          </span>
                        ) : (
                          <span className="text-emerald-400 flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3" /> None
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      )}

      {/* Trigger Ingestion Modal */}
      {showTriggerModal && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
        >
          <div className="w-full max-w-md rounded-xl border border-slate-700 bg-slate-900 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Play className="h-4 w-4 text-indigo-400" /> Launch Ingestion Job
              </h3>
              <button
                onClick={() => setShowTriggerModal(false)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleLaunchJob} className="space-y-4 text-xs">
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={forceReingest}
                    onChange={(e) => setForceReingest(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Force Re-ingest (overwrite existing meeting records)</span>
                </label>

                <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={skipEmbeddings}
                    onChange={(e) => setSkipEmbeddings(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Skip Embeddings (faster text-only parsing)</span>
                </label>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400">Limit Files (Optional testing limit):</label>
                <input
                  type="number"
                  placeholder="Leave empty for all 138 transcripts"
                  value={limitFiles}
                  onChange={(e) => setLimitFiles(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-slate-100 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowTriggerModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={triggering} className="gap-1.5">
                  {triggering ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                  <span>{triggering ? "Starting..." : "Start Ingestion"}</span>
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
