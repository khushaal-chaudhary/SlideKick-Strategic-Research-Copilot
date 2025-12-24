"use client";

import { useBackendStatus, BackendStatus } from "@/hooks/use-backend-status";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, WifiOff } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const statusConfig: Record<
  BackendStatus,
  {
    label: string;
    icon: React.ReactNode;
    variant: "default" | "secondary" | "destructive" | "outline";
    className: string;
  }
> = {
  ready: {
    label: "Ready",
    icon: <CheckCircle2 className="h-3 w-3" />,
    variant: "secondary",
    className: "bg-green-500/10 text-green-600 border-green-500/20 hover:bg-green-500/20",
  },
  starting: {
    label: "Starting",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
    variant: "secondary",
    className: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20 hover:bg-yellow-500/20",
  },
  offline: {
    label: "Offline",
    icon: <WifiOff className="h-3 w-3" />,
    variant: "secondary",
    className: "bg-red-500/10 text-red-600 border-red-500/20 hover:bg-red-500/20",
  },
  checking: {
    label: "Checking",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
    variant: "outline",
    className: "",
  },
};

export function StatusIndicator() {
  const { status, lastChecked, loadingMessage, refresh } = useBackendStatus();
  const config = statusConfig[status];

  const getTooltipContent = () => {
    switch (status) {
      case "ready":
        return "Backend is up and ready to kick!";
      case "starting":
        return loadingMessage || "Backend is warming up...";
      case "offline":
        return "Backend is offline. It might be sleeping on HF Spaces.";
      case "checking":
        return "Checking backend status...";
    }
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button onClick={refresh} className="focus:outline-none">
            <Badge
              variant={config.variant}
              className={`gap-1.5 cursor-pointer transition-colors ${config.className}`}
            >
              {config.icon}
              <span className="hidden sm:inline">{config.label}</span>
            </Badge>
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <p className="text-sm">{getTooltipContent()}</p>
          {lastChecked && (
            <p className="text-xs text-muted-foreground mt-1">
              Last checked: {lastChecked.toLocaleTimeString()}
            </p>
          )}
          <p className="text-xs text-muted-foreground mt-1">
            Click to refresh
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
