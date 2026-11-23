import { useSystemStatus } from "../hooks/useSystemStatus";
import { Badge } from "./ui/badge";

export function StatusIndicator() {
  const { connectionState } = useSystemStatus();

  switch (connectionState) {
    case "healthy":
      return (
        <Badge variant="success" className="gap-1.5 py-1 px-3">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          System Operational
        </Badge>
      );
    case "degraded":
      return (
        <Badge variant="warning" className="gap-1.5 py-1 px-3">
          <span className="h-2 w-2 rounded-full bg-amber-400" />
          Database Offline
        </Badge>
      );
    case "loading":
      return (
        <Badge variant="outline" className="gap-1.5 py-1 px-3">
          <span className="h-2 w-2 rounded-full bg-slate-400 animate-pulse" />
          Connecting...
        </Badge>
      );
    case "error":
    default:
      return (
        <Badge variant="destructive" className="gap-1.5 py-1 px-3">
          <span className="h-2 w-2 rounded-full bg-rose-400" />
          API Disconnected
        </Badge>
      );
  }
}

