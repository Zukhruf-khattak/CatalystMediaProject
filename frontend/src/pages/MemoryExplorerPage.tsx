import { useState, useEffect } from "react";
import {
  Layers,
  Search,
  Filter,
  Eye,
  GitCommit,
  Loader2,
  AlertCircle,
  Database,
  ArrowRight,
} from "lucide-react";
import { searchMemories } from "../lib/api";
import { MemoryResponse, MemorySearchFilter } from "../types/memory";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { CitationContextModal } from "../components/CitationContextModal";

export function MemoryExplorerPage() {
  const [memories, setMemories] = useState<MemoryResponse[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [teamCode, setTeamCode] = useState<string>("TS3006");
  const [memoryType, setMemoryType] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [queryText, setQueryText] = useState<string>("");

  // Modal context inspection
  const [inspectMemory, setInspectMemory] = useState<MemoryResponse | null>(null);

  const fetchFilteredMemories = async () => {
    setLoading(true);
    setError(null);
    try {
      const filter: MemorySearchFilter = {
        limit: 50,
      };
      if (teamCode) filter.team_code = teamCode;
      if (memoryType) filter.memory_type = memoryType;
      if (statusFilter) filter.status = statusFilter;
      if (queryText.trim()) filter.query_text = queryText.trim();

      const res = await searchMemories(filter);
      setMemories(res.items);
      setTotalCount(res.total_count);
    } catch (err: any) {
      setError(err.message || "Failed to search memories");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFilteredMemories();
  }, [teamCode, memoryType, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchFilteredMemories();
  };

  const getMemoryTypeBadgeVariant = (type: string) => {
    switch (type.toUpperCase()) {
      case "DECISION":
        return "default";
      case "ACTION":
        return "warning";
      case "DISAGREEMENT":
        return "destructive";
      default:
        return "outline";
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status.toLowerCase()) {
      case "current":
      case "resolved":
        return "success";
      case "open":
        return "warning";
      case "superseded":
      case "rejected":
        return "outline";
      default:
        return "default";
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
          <Layers className="h-3.5 w-3.5" /> Temporal Knowledge Graph
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Temporal Memory Explorer
        </h1>
        <p className="text-slate-400 text-sm max-w-3xl leading-relaxed">
          Explore atomic records of decisions, actions, requirements, and disagreements extracted
          across sequential meetings. Inspect temporal relationships (supports, updates, supersedes)
          and verify verbatim quotations directly in the transcript.
        </p>
      </div>

      {/* Filter Controls Card */}
      <Card className="border-slate-800">
        <CardContent className="pt-6">
          <form onSubmit={handleSearchSubmit} className="space-y-4">
            <div className="flex flex-col md:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search statements or verbatim quotes..."
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950/80 pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <Button type="submit" disabled={loading} className="gap-2 shrink-0">
                <Filter className="h-4 w-4" />
                <span>Apply Filters</span>
              </Button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-800/80">
              {/* Team Filter */}
              <div className="space-y-1">
                <label className="text-xs text-slate-400">Team Code</label>
                <select
                  value={teamCode}
                  onChange={(e) => setTeamCode(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">All Teams</option>
                  <option value="TS3006">TS3006</option>
                  <option value="TS3012">TS3012</option>
                  <option value="TS3011">TS3011</option>
                  <option value="TS3009">TS3009</option>
                  <option value="ES2003">ES2003</option>
                </select>
              </div>

              {/* Memory Type Filter */}
              <div className="space-y-1">
                <label className="text-xs text-slate-400">Memory Type</label>
                <select
                  value={memoryType}
                  onChange={(e) => setMemoryType(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">All Types</option>
                  <option value="DECISION">DECISION</option>
                  <option value="ACTION">ACTION</option>
                  <option value="REQUIREMENT">REQUIREMENT</option>
                  <option value="DISAGREEMENT">DISAGREEMENT</option>
                  <option value="PREFERENCE">PREFERENCE</option>
                  <option value="ENTITY">ENTITY</option>
                </select>
              </div>

              {/* Status Filter */}
              <div className="space-y-1">
                <label className="text-xs text-slate-400">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">All Statuses</option>
                  <option value="current">Current / Active</option>
                  <option value="superseded">Superseded / Replaced</option>
                  <option value="open">Open (Actions/Disputes)</option>
                  <option value="resolved">Resolved</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>
          Showing <span className="font-semibold text-slate-200">{memories.length}</span> of{" "}
          <span className="font-semibold text-slate-200">{totalCount}</span> memory records
        </span>
        <span className="font-mono text-[11px]">PostgreSQL Persistent Memory Store</span>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="py-16 flex flex-col items-center justify-center gap-3 text-slate-400">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
          <span className="text-sm">Querying temporal memory store...</span>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-400 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-rose-200">Memory Query Failed</p>
            <p className="text-rose-300 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && memories.length === 0 && (
        <Card className="border-slate-800 text-center py-12">
          <CardContent className="space-y-3">
            <Database className="h-10 w-10 text-slate-600 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-300">No Memories Found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No temporal memories match your current filter criteria. Try choosing a different team or clearing the search query.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Memories Grid */}
      {!loading && memories.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {memories.map((mem) => (
            <Card
              key={mem.id}
              className="border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between"
            >
              <CardContent className="p-5 space-y-4">
                {/* Card Top Row */}
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={getMemoryTypeBadgeVariant(mem.memory_type)} className="text-[10px]">
                      {mem.memory_type}
                    </Badge>
                    <Badge variant={getStatusBadgeVariant(mem.status)} className="text-[10px]">
                      {mem.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                    <span className="text-indigo-400 font-semibold">
                      {mem.sequence_letter.toUpperCase()} (Order {mem.meeting_order})
                    </span>
                  </div>
                </div>

                {/* Statement */}
                <div className="space-y-1">
                  <h3 className="text-sm font-semibold text-slate-100 leading-snug">
                    {mem.statement}
                  </h3>
                  <div className="text-xs text-slate-400">
                    Speaker: <span className="text-slate-300">{mem.speaker_label}</span>
                    {mem.speaker_role && <span> ({mem.speaker_role})</span>}
                  </div>
                </div>

                {/* Verbatim Quotation */}
                <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 space-y-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Supporting Transcript Quote
                  </span>
                  <p className="text-xs italic text-slate-300 font-serif leading-relaxed">
                    "{mem.quote}"
                  </p>
                </div>

                {/* Relationships */}
                {mem.outgoing_relationships && mem.outgoing_relationships.length > 0 && (
                  <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
                    <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                      <GitCommit className="h-3 w-3 text-indigo-400" />
                      Temporal Relationships:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {mem.outgoing_relationships.map((rel) => (
                        <span
                          key={rel.id}
                          className="inline-flex items-center gap-1 rounded bg-indigo-950/40 border border-indigo-500/20 px-2 py-0.5 text-[10px] text-indigo-300 font-mono"
                        >
                          <span className="font-semibold uppercase">{rel.relationship_type}</span>
                          <ArrowRight className="h-2.5 w-2.5 text-indigo-400" />
                          <span>{rel.target_memory_id.slice(0, 6)}...</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>

              {/* Card Footer */}
              <div className="border-t border-slate-800/80 bg-slate-950/40 px-5 py-2.5 flex items-center justify-between text-xs text-slate-400">
                <span className="font-mono text-[10px]">ID: {mem.id.slice(0, 8)}...</span>
                {mem.turn_id && (
                  <button
                    type="button"
                    onClick={() => setInspectMemory(mem)}
                    className="flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    <span>Inspect Turn Context</span>
                  </button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Interactive Turn Context Modal */}
      {inspectMemory && (
        <CitationContextModal
          turnId={inspectMemory.turn_id || null}
          quote={inspectMemory.quote}
          meetingId={inspectMemory.sequence_letter ? `Meeting ${inspectMemory.sequence_letter}` : "Memory Turn"}
          speakerLabel={inspectMemory.speaker_label}
          speakerRole={inspectMemory.speaker_role}
          onClose={() => setInspectMemory(null)}
        />
      )}
    </div>
  );
}
