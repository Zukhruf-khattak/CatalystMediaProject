export interface HealthResponse {
  status: "healthy";
  app_name: string;
  version: string;
  environment: string;
}

export interface ReadyResponse {
  status: "ready" | "degraded";
  database: boolean;
  app_name: string;
  version: string;
  environment: string;
}

export type ConnectionState = "loading" | "healthy" | "degraded" | "error";

export interface PhaseInfo {
  id: string;
  number: string;
  title: string;
  status: "ready" | "in_progress" | "completed" | "planned";
  description: string;
}
