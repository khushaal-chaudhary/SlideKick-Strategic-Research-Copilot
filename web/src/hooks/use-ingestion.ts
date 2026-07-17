"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { API_CONFIG } from "@/lib/constants";
import { getWorkspaceId } from "@/lib/workspace";
import type { ErrorInfo, RateLimitInfo } from "@/components/error-banner";

export interface IngestionProgress {
  stage: string;
  message: string;
  done?: number;
  total?: number;
}

export interface WorkspaceStats {
  workspace_id: string;
  documents: string[];
  entities: number;
  chunks: number;
}

interface IngestionState {
  isUploading: boolean;
  progress: IngestionProgress | null;
  stats: WorkspaceStats | null;
  error: ErrorInfo | null;
}

export function useIngestion() {
  const [state, setState] = useState<IngestionState>({
    isUploading: false,
    progress: null,
    stats: null,
    error: null,
  });

  const eventSourceRef = useRef<EventSource | null>(null);

  const refreshStats = useCallback(async () => {
    try {
      const workspaceId = getWorkspaceId();
      if (!workspaceId) return;
      const res = await fetch(
        `${API_CONFIG.baseUrl}${API_CONFIG.documentsEndpoint}/${workspaceId}`
      );
      if (!res.ok) return;
      const stats: WorkspaceStats = await res.json();
      setState((prev) => ({ ...prev, stats }));
    } catch {
      // API offline or workspace empty — leave stats as-is
    }
  }, []);

  useEffect(() => {
    refreshStats();
    return () => {
      eventSourceRef.current?.close();
    };
  }, [refreshStats]);

  const upload = useCallback(
    async (file: File) => {
      setState((prev) => ({
        ...prev,
        isUploading: true,
        progress: { stage: "uploading", message: `Uploading ${file.name}...` },
        error: null,
      }));

      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("workspace_id", getWorkspaceId());

        const res = await fetch(
          `${API_CONFIG.baseUrl}${API_CONFIG.documentsEndpoint}/upload`,
          { method: "POST", body: formData }
        );

        if (!res.ok) {
          const body = await res.json().catch(() => null);
          throw new Error(body?.detail || `Upload failed (${res.status})`);
        }

        const { stream_url } = await res.json();

        const eventSource = new EventSource(`${API_CONFIG.baseUrl}${stream_url}`);
        eventSourceRef.current = eventSource;

        eventSource.onmessage = (event) => {
          let data: {
            type: string;
            stage?: string;
            message?: string;
            done?: number;
            total?: number;
            error?: string;
            error_type?: "rate_limit" | "general";
            rate_limit?: RateLimitInfo;
            nodes?: number;
            relationships?: number;
            chunks?: number;
          };
          try {
            data = JSON.parse(event.data);
          } catch {
            return;
          }

          switch (data.type) {
            case "ingest_progress":
              setState((prev) => ({
                ...prev,
                progress: {
                  stage: data.stage || "processing",
                  message: data.message || "",
                  done: data.done,
                  total: data.total,
                },
              }));
              break;

            case "ingest_complete":
              eventSource.close();
              setState((prev) => ({
                ...prev,
                isUploading: false,
                progress: {
                  stage: "complete",
                  message: `Added ${data.nodes ?? 0} entities, ${data.relationships ?? 0} relationships, ${data.chunks ?? 0} searchable chunks`,
                },
              }));
              refreshStats();
              break;

            case "error":
              eventSource.close();
              setState((prev) => ({
                ...prev,
                isUploading: false,
                progress: null,
                error: {
                  message: data.error || "Ingestion failed",
                  error_type: data.error_type || "general",
                  rate_limit: data.rate_limit,
                },
              }));
              break;
          }
        };

        eventSource.onerror = () => {
          eventSource.close();
          setState((prev) =>
            prev.isUploading
              ? {
                  ...prev,
                  isUploading: false,
                  progress: null,
                  error: {
                    message: "Connection lost during ingestion. Please try again.",
                    error_type: "general",
                  },
                }
              : prev
          );
        };
      } catch (error) {
        setState((prev) => ({
          ...prev,
          isUploading: false,
          progress: null,
          error: {
            message: error instanceof Error ? error.message : "Upload failed",
            error_type: "general",
          },
        }));
      }
    },
    [refreshStats]
  );

  const removeDocuments = useCallback(async () => {
    try {
      const workspaceId = getWorkspaceId();
      await fetch(
        `${API_CONFIG.baseUrl}${API_CONFIG.documentsEndpoint}/${workspaceId}`,
        { method: "DELETE" }
      );
      setState((prev) => ({ ...prev, stats: null, progress: null }));
    } catch {
      setState((prev) => ({
        ...prev,
        error: {
          message: "Failed to remove documents. Please try again.",
          error_type: "general",
        },
      }));
    }
  }, []);

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  const hasDocuments = (state.stats?.documents.length ?? 0) > 0;

  return {
    ...state,
    hasDocuments,
    upload,
    removeDocuments,
    clearError,
  };
}
