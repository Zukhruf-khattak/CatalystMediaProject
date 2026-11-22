import { StatusIndicator } from "./StatusIndicator";
import { Sparkles } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-white tracking-tight">
              Catalist Meeting Intelligence
            </h1>
            <p className="text-xs text-slate-400 hidden sm:block">
              AMI Corpus Memory Store & Team Briefing Agent
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <StatusIndicator />
        </div>
      </div>
    </header>
  );
}
