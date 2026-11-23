import { Link } from "react-router-dom";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { Button } from "../components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
      <div className="rounded-full bg-slate-900 border border-slate-800 p-4 text-slate-400">
        <AlertCircle className="h-8 w-8 text-amber-400" />
      </div>
      <h2 className="text-xl font-semibold text-white">Page Not Found</h2>
      <p className="text-sm text-slate-400 max-w-sm">
        The requested view does not exist or has not yet been implemented in this phase.
      </p>
      <Link to="/">
        <Button variant="outline" size="sm" className="gap-2">
          <ArrowLeft className="h-4 w-4" /> Return to Overview
        </Button>
      </Link>
    </div>
  );
}

