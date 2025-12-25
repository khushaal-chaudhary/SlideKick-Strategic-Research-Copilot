"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { FileText, CheckCircle2, BarChart3 } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface ResponseViewerProps {
  response: string | null;
  isLoading?: boolean;
  qualityScore?: number;
  sources?: string[];
}

export function ResponseViewer({
  response,
  isLoading = false,
  qualityScore,
  sources,
}: ResponseViewerProps) {
  if (!response && !isLoading) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="border-border/50 shadow-subtle">
        <CardHeader className="py-4 px-5 border-b">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Research Response
            </CardTitle>
            <div className="flex items-center gap-2">
              {qualityScore !== undefined && (
                <Badge variant="secondary" className="gap-1">
                  <BarChart3 className="h-3 w-3" />
                  {Math.round(qualityScore * 100)}% quality
                </Badge>
              )}
              <Badge variant="outline" className="gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Complete
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <div className="max-h-[500px] overflow-y-auto">
            <div className="p-5 prose prose-sm max-w-none dark:prose-invert prose-headings:font-semibold prose-headings:tracking-tight prose-h2:text-lg prose-h3:text-base prose-p:text-muted-foreground prose-li:text-muted-foreground prose-strong:text-foreground break-words [overflow-wrap:anywhere]">
              <ReactMarkdown
                components={{
                  a: ({ children, ...props }) => (
                    <a {...props} className="break-all">
                      {children}
                    </a>
                  ),
                  code: ({ children, ...props }) => (
                    <code {...props} className="break-all">
                      {children}
                    </code>
                  ),
                }}
              >
                {response || ""}
              </ReactMarkdown>
            </div>
          </div>

          {sources && sources.length > 0 && (
            <div className="px-5 py-3 border-t bg-secondary">
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span className="font-medium shrink-0">Sources:</span>
                <div className="flex flex-wrap gap-1.5">
                  {sources.map((source) => (
                    <Badge key={source} variant="outline" className="text-xs">
                      {source}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
