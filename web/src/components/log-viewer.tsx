"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Search,
  Brain,
  Target,
  Sparkles,
  FileText,
  Lightbulb,
  TrendingUp,
} from "lucide-react";

export interface LogEvent {
  id: string;
  type: string;
  node?: string;
  message: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

interface LogViewerProps {
  events: LogEvent[];
  isActive?: boolean;
}

const nodeIcons: Record<string, React.ReactNode> = {
  planner: <FileText className="h-4 w-4" />,
  retriever: <Search className="h-4 w-4" />,
  analyzer: <Brain className="h-4 w-4" />,
  critic: <Target className="h-4 w-4" />,
  generator: <Sparkles className="h-4 w-4" />,
  responder: <CheckCircle2 className="h-4 w-4" />,
};

const nodeColors: Record<string, string> = {
  planner: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  retriever: "bg-green-500/10 text-green-600 border-green-500/20",
  analyzer: "bg-purple-500/10 text-purple-600 border-purple-500/20",
  critic: "bg-orange-500/10 text-orange-600 border-orange-500/20",
  generator: "bg-pink-500/10 text-pink-600 border-pink-500/20",
  responder: "bg-teal-500/10 text-teal-600 border-teal-500/20",
};

function getEventIcon(event: LogEvent) {
  if (event.type === "node_start" || event.type === "node_complete") {
    return event.node ? nodeIcons[event.node] : <Activity className="h-4 w-4" />;
  }
  if (event.type === "insight") return <Lightbulb className="h-4 w-4 text-yellow-500" />;
  if (event.type === "retrieval") return <TrendingUp className="h-4 w-4 text-green-500" />;
  if (event.type === "decision") return <Target className="h-4 w-4 text-orange-500" />;
  if (event.type === "error") return <AlertCircle className="h-4 w-4 text-red-500" />;
  if (event.type === "complete") return <CheckCircle2 className="h-4 w-4 text-green-500" />;
  return <Activity className="h-4 w-4" />;
}

function formatTime(timestamp: string) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function LogViewer({ events, isActive = false }: LogViewerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <Card className="h-full flex flex-col border-border/50">
      <CardHeader className="py-4 px-5 border-b">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Agent Logs
          </CardTitle>
          {isActive && (
            <Badge variant="secondary" className="gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              Processing
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 overflow-hidden">
        <ScrollArea className="h-full" ref={scrollRef}>
          <div className="p-4 space-y-3">
            {events.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                <Activity className="h-8 w-8 mb-3 opacity-50" />
                <p className="text-sm">Submit a query to see agent activity</p>
              </div>
            ) : (
              <AnimatePresence mode="popLayout">
                {events.map((event) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                    className="group"
                  >
                    <div className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div
                          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${
                            event.node
                              ? nodeColors[event.node] ||
                                "bg-secondary text-foreground"
                              : "bg-secondary text-muted-foreground"
                          }`}
                        >
                          {getEventIcon(event)}
                        </div>
                        <div className="w-px flex-1 bg-border/50 mt-2" />
                      </div>

                      <div className="flex-1 pb-4">
                        <div className="flex items-center gap-2">
                          {event.node && (
                            <span className="text-sm font-medium capitalize">
                              {event.node}
                            </span>
                          )}
                          <span className="text-xs text-muted-foreground">
                            {formatTime(event.timestamp)}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {event.message}
                        </p>

                        {/* Show metadata for special events */}
                        {event.type === "insight" && event.metadata && (
                          <div className="mt-2 p-2 rounded-md bg-yellow-500/5 border border-yellow-500/20">
                            <div className="flex items-center gap-1.5">
                              <Lightbulb className="h-3.5 w-3.5 text-yellow-500" />
                              <span className="text-xs font-medium text-yellow-700">
                                {(event.metadata as { title?: string }).title}
                              </span>
                            </div>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {(event.metadata as { description?: string }).description}
                            </p>
                          </div>
                        )}

                        {event.type === "retrieval" && event.metadata && (
                          <div className="mt-2 p-2 rounded-md bg-green-500/5 border border-green-500/20">
                            <div className="flex items-center gap-1.5">
                              <Search className="h-3.5 w-3.5 text-green-500" />
                              <span className="text-xs font-medium text-green-700">
                                {(event.metadata as { result_count?: number }).result_count} results from{" "}
                                {(event.metadata as { source?: string }).source}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
