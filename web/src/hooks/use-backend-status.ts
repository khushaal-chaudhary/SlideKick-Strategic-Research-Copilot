"use client";

import { useState, useEffect, useCallback } from "react";
import { API_CONFIG, LOADING_MESSAGES } from "@/lib/constants";

export type BackendStatus = "ready" | "starting" | "offline" | "checking";

interface BackendHealth {
  status: string;
  service: string;
  version: string;
  model_loaded?: boolean;
}

export function useBackendStatus(pollInterval = 10000) {
  const [status, setStatus] = useState<BackendStatus>("checking");
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [loadingMessage, setLoadingMessage] = useState<string>("");

  const getRandomLoadingMessage = useCallback(() => {
    const index = Math.floor(Math.random() * LOADING_MESSAGES.length);
    return LOADING_MESSAGES[index];
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(
        `${API_CONFIG.baseUrl}${API_CONFIG.healthEndpoint}`,
        {
          method: "GET",
          signal: controller.signal,
        }
      );

      clearTimeout(timeoutId);

      if (response.ok) {
        const data: BackendHealth = await response.json();

        if (data.status === "healthy") {
          // Check if model is loaded (for when we integrate real agent)
          if (data.model_loaded === false) {
            setStatus("starting");
            setLoadingMessage(getRandomLoadingMessage());
          } else {
            setStatus("ready");
            setLoadingMessage("");
          }
        } else {
          setStatus("starting");
          setLoadingMessage(getRandomLoadingMessage());
        }
      } else {
        setStatus("offline");
        setLoadingMessage("");
      }
    } catch {
      // Network error or timeout
      setStatus("offline");
      setLoadingMessage("");
    }

    setLastChecked(new Date());
  }, [getRandomLoadingMessage]);

  useEffect(() => {
    // Initial check
    checkHealth();

    // Set up polling
    const interval = setInterval(checkHealth, pollInterval);

    return () => clearInterval(interval);
  }, [checkHealth, pollInterval]);

  return {
    status,
    lastChecked,
    loadingMessage,
    refresh: checkHealth,
  };
}
