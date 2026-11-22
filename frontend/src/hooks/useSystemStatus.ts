import { useQuery } from "@tanstack/react-query";
import { fetchHealth, fetchReady } from "../lib/api";
import { ConnectionState, HealthResponse, ReadyResponse } from "../types/status";

export function useHealthQuery() {
  return useQuery<HealthResponse, Error>({
    queryKey: ["system", "health"],
    queryFn: fetchHealth,
    refetchInterval: 10000,
    retry: false,
  });
}

export function useReadyQuery() {
  return useQuery<ReadyResponse, Error>({
    queryKey: ["system", "ready"],
    queryFn: fetchReady,
    refetchInterval: 10000,
    retry: false,
  });
}

export function useSystemStatus() {
  const healthQuery = useHealthQuery();
  const readyQuery = useReadyQuery();

  const isPending = healthQuery.isPending || readyQuery.isPending;
  const isError = healthQuery.isError || readyQuery.isError;

  let connectionState: ConnectionState = "loading";

  if (isError) {
    connectionState = "error";
  } else if (isPending) {
    connectionState = "loading";
  } else if (readyQuery.data?.database === false || readyQuery.data?.status === "degraded") {
    connectionState = "degraded";
  } else if (healthQuery.data?.status === "healthy" && readyQuery.data?.database === true) {
    connectionState = "healthy";
  } else {
    connectionState = "error";
  }

  return {
    connectionState,
    health: healthQuery.data,
    ready: readyQuery.data,
    isLoading: isPending,
    isError,
    error: healthQuery.error || readyQuery.error,
    refetch: () => {
      healthQuery.refetch();
      readyQuery.refetch();
    },
  };
}
