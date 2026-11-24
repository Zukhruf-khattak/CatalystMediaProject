import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "../components/Layout";
import { OverviewPage } from "../pages/OverviewPage";
import { ResearchAssistantPage } from "../pages/ResearchAssistantPage";
import { CitationViewerPage } from "../pages/CitationViewerPage";
import { MemoryExplorerPage } from "../pages/MemoryExplorerPage";
import { DecisionTimelinePage } from "../pages/DecisionTimelinePage";
import { BriefingPage } from "../pages/BriefingPage";
import { IngestionPage } from "../pages/IngestionPage";
import { EvaluationPage } from "../pages/EvaluationPage";
import { NotFoundPage } from "../pages/NotFoundPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<OverviewPage />} />
            <Route path="research" element={<ResearchAssistantPage />} />
            <Route path="questions" element={<Navigate to="/research" replace />} />
            <Route path="citations" element={<CitationViewerPage />} />
            <Route path="memory" element={<MemoryExplorerPage />} />
            <Route path="decisions" element={<DecisionTimelinePage />} />
            <Route path="timeline" element={<Navigate to="/decisions" replace />} />
            <Route path="briefing" element={<BriefingPage />} />
            <Route path="briefings" element={<Navigate to="/briefing" replace />} />
            <Route path="ingestion" element={<IngestionPage />} />
            <Route path="evaluation" element={<EvaluationPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
