"use client";

import { useState, useCallback, useRef } from "react";
import { API_CONFIG } from "@/lib/constants";
import type { LogEvent } from "@/components/log-viewer";
import type { ErrorInfo, RateLimitInfo } from "@/components/error-banner";

export type LLMProvider = "ollama" | "groq";

interface ResearchState {
  isLoading: boolean;
  events: LogEvent[];
  response: string | null;
  qualityScore: number | null;
  sources: string[];
  error: ErrorInfo | null;
}

export function useResearch() {
  const [state, setState] = useState<ResearchState>({
    isLoading: false,
    events: [],
    response: null,
    qualityScore: null,
    sources: [],
    error: null,
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const eventIdCounter = useRef(0);

  const addEvent = useCallback(
    (
      type: string,
      message: string,
      node?: string,
      metadata?: Record<string, unknown>
    ) => {
      const event: LogEvent = {
        id: `event-${eventIdCounter.current++}`,
        type,
        node,
        message,
        timestamp: new Date().toISOString(),
        metadata,
      };

      setState((prev) => ({
        ...prev,
        events: [...prev.events, event],
      }));
    },
    []
  );

  const submitQuery = useCallback(
    async (query: string, llmProvider: LLMProvider = "ollama") => {
      // Reset state
      setState({
        isLoading: true,
        events: [],
        response: null,
        qualityScore: null,
        sources: [],
        error: null,
      });
      eventIdCounter.current = 0;

      try {
        // Submit query to get session ID
        const submitResponse = await fetch(
          `${API_CONFIG.baseUrl}${API_CONFIG.queryEndpoint}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ query, llm_provider: llmProvider }),
          }
        );

        if (!submitResponse.ok) {
          throw new Error("Failed to submit query");
        }

        const { session_id } = await submitResponse.json();

        // Connect to SSE stream
        const eventSource = new EventSource(
          `${API_CONFIG.baseUrl}${API_CONFIG.streamEndpoint}/${session_id}`
        );
        eventSourceRef.current = eventSource;

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            handleSSEEvent(data);
          } catch (e) {
            console.error("Failed to parse SSE event:", e);
          }
        };

        eventSource.onerror = (error) => {
          console.error("SSE error:", error);
          eventSource.close();
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: {
              message: "Connection error occurred. Please check your network and try again.",
              error_type: "general",
            },
          }));
        };

        // Handle specific event types
        const handleSSEEvent = (data: {
          type: string;
          node?: string;
          message?: string;
          error?: string;
          error_type?: "rate_limit" | "general";
          rate_limit?: RateLimitInfo;
          response?: string;
          quality_score?: number;
          sources_used?: string[];
          title?: string;
          description?: string;
          confidence?: number;
          source?: string;
          result_count?: number;
          decision?: string;
          reasoning?: string;
          [key: string]: unknown;
        }) => {
          switch (data.type) {
            case "start":
              addEvent("start", `Starting research: ${query}`);
              break;

            case "node_start":
            case "node_complete":
              addEvent(data.type, data.message || "", data.node);
              break;

            case "progress":
              addEvent("progress", data.message || "");
              break;

            case "retrieval":
              addEvent("retrieval", data.message || `Retrieved data from ${data.source}`, undefined, {
                source: data.source,
                result_count: data.result_count,
              });
              break;

            case "insight":
              addEvent("insight", data.description || "", undefined, {
                title: data.title,
                description: data.description,
                confidence: data.confidence,
              });
              break;

            case "decision":
              addEvent("decision", `${data.decision}: ${data.reasoning}`);
              break;

            case "final_response":
              setState((prev) => ({
                ...prev,
                response: data.response || null,
                qualityScore: data.quality_score || null,
                sources: data.sources_used || [],
              }));
              addEvent("complete", "Research complete");
              break;

            case "complete":
              eventSource.close();
              setState((prev) => ({
                ...prev,
                isLoading: false,
              }));
              break;

            case "error":
              addEvent("error", data.error || data.message || "An error occurred");
              eventSource.close();
              setState((prev) => ({
                ...prev,
                isLoading: false,
                error: {
                  message: data.error || data.message || "An error occurred",
                  error_type: data.error_type || "general",
                  rate_limit: data.rate_limit,
                },
              }));
              break;
          }
        };
      } catch (error) {
        console.error("Research error:", error);
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: {
            message: error instanceof Error ? error.message : "Unknown error",
            error_type: "general",
          },
        }));
      }
    },
    [addEvent]
  );

  const reset = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setState({
      isLoading: false,
      events: [],
      response: null,
      qualityScore: null,
      sources: [],
      error: null,
    });
    eventIdCounter.current = 0;
  }, []);

  const clearError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      error: null,
    }));
  }, []);

  return {
    ...state,
    submitQuery,
    reset,
    clearError,
  };
}
