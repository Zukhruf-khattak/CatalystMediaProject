import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Sparkles,
  Quote,
  Layers,
  GitBranch,
  FileText,
  HardDrive,
  BarChart3,
} from "lucide-react";
import { cn } from "../lib/utils";

const navigationItems = [
  {
    name: "Overview & Status",
    href: "/",
    icon: LayoutDashboard,
    badge: "Phase 1",
  },
  {
    name: "Research Assistant",
    href: "/research",
    icon: Sparkles,
    badge: "Phase 5",
  },
  {
    name: "Citation Context",
    href: "/citations",
    icon: Quote,
    badge: "Phase 6",
  },
  {
    name: "Memory Explorer",
    href: "/memory",
    icon: Layers,
    badge: "Phase 3",
  },
  {
    name: "Decision Timeline",
    href: "/decisions",
    icon: GitBranch,
    badge: "Phase 3",
  },
  {
    name: "TS3012 Briefing",
    href: "/briefing",
    icon: FileText,
    badge: "Phase 7",
  },
  {
    name: "Meeting Ingestion",
    href: "/ingestion",
    icon: HardDrive,
    badge: "Phase 2",
  },
  {
    name: "Evaluation Benchmark",
    href: "/evaluation",
    icon: BarChart3,
    badge: "Phase 4 & 6",
  },
];

export function Sidebar() {
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between hidden md:flex shrink-0">
      <div className="space-y-6">
        <div>
          <h2 className="px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Intelligence Platform
          </h2>
          <nav className="mt-3 space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-indigo-600/10 text-indigo-400 font-semibold"
                        : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                    )
                  }
                >
                  <div className="flex items-center gap-3">
                    <Icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[10px] font-semibold tracking-wider text-slate-400 border border-slate-800 rounded px-1.5 py-0.5 bg-slate-900">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="border-t border-slate-800/80 pt-4 px-3">
        <div className="text-xs text-slate-400">
          <p className="font-medium text-slate-400">Catalist Meeting Intelligence</p>
          <p className="mt-0.5">Production UI · Phase 8</p>
        </div>
      </div>
    </aside>
  );
}
