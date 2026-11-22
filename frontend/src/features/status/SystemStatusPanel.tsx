import { RefreshCw, Server, Database, CheckCircle2, AlertTriangle, XCircle, Clock } from "lucide-react";
import { useSystemStatus } from "../../hooks/useSystemStatus";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";

export function SystemStatusPanel() {
  const { connectionState, health, ready, isLoading, isError, error, refetch } = useSystemStatus();

  return (
    <Card className="border-slate-800">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <div>
          <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
            System & Infrastructure Status
          </CardTitle>
          <CardDescription>
            Live connectivity telemetry queried directly from FastAPI foundation endpoints.
          </CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isLoading}
          aria-label="Refresh status"
          className="gap-2 text-xs"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Connection Banner */}
        {connectionState === "healthy" && (
          <div className="flex items-center gap-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-sm text-emerald-300">
            <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
            <div>
              <p className="font-medium">All Foundation Systems Operational</p>
              <p className="text-xs text-emerald-400/80">
                Backend API process is healthy and PostgreSQL 16 + pgvector responded to ping.
              </p>
            </div>
          </div>
        )}

        {connectionState === "degraded" && (
          <div className="flex items-center gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3.5 text-sm text-amber-300">
            <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
            <div>
              <p className="font-medium">Database Degraded</p>
              <p className="text-xs text-amber-400/80">
                FastAPI is running, but PostgreSQL did not respond within the 5.0s probe timeout. Start container with: <code className="bg-slate-900 px-1 py-0.5 rounded text-amber-200">docker-compose up -d db</code>
              </p>
            </div>
          </div>
        )}

        {connectionState === "error" && (
          <div className="flex items-center gap-3 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3.5 text-sm text-rose-300">
            <XCircle className="h-5 w-5 text-rose-400 shrink-0" />
            <div>
              <p className="font-medium">Backend API Unreachable</p>
              <p className="text-xs text-rose-400/80">
                Failed to connect to <code className="bg-slate-900 px-1 py-0.5 rounded text-rose-200">/api/v1/health</code>. Ensure the FastAPI service is running locally on port 8000. {error ? `(${error.message})` : ""}
              </p>
            </div>
          </div>
        )}

        {connectionState === "loading" && (
          <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-900/40 p-3.5 text-sm text-slate-300">
            <Clock className="h-5 w-5 text-slate-400 animate-pulse shrink-0" />
            <p className="text-xs">Querying backend readiness probes...</p>
          </div>
        )}

        {/* Detailed Dependency Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Backend Card */}
          <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm font-medium text-slate-200">
                <Server className="h-4 w-4 text-indigo-400" />
                Backend API (/api/v1/health)
              </span>
              {health?.status === "healthy" ? (
                <Badge variant="success">200 OK</Badge>
              ) : isError ? (
                <Badge variant="destructive">Offline</Badge>
              ) : (
                <Badge variant="outline">Checking...</Badge>
              )}
            </div>
            <div className="text-xs text-slate-400 space-y-1">
              <p>App Name: <span className="text-slate-200">{health?.app_name || "—"}</span></p>
              <p>Version: <span className="text-slate-200">{health?.version || "—"}</span></p>
              <p>Environment: <span className="text-slate-200 capitalize">{health?.environment || "—"}</span></p>
            </div>
          </div>

          {/* Database Card */}
          <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm font-medium text-slate-200">
                <Database className="h-4 w-4 text-indigo-400" />
                PostgreSQL 16 + pgvector (/api/v1/ready)
              </span>
              {ready?.database ? (
                <Badge variant="success">Connected</Badge>
              ) : connectionState === "degraded" ? (
                <Badge variant="warning">503 Timeout</Badge>
              ) : (
                <Badge variant="outline">Checking...</Badge>
              )}
            </div>
            <div className="text-xs text-slate-400 space-y-1">
              <p>Status: <span className="text-slate-200 capitalize">{ready?.status || "—"}</span></p>
              <p>Connection: <span className="text-slate-200">{ready?.database ? "Healthy (SELECT 1)" : "Disconnected"}</span></p>
              <p>Target Extension: <span className="text-slate-200 font-mono text-[11px]">pgvector (384-dim)</span></p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
