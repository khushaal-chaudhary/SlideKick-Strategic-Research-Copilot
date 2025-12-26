"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { FileText, CheckCircle2, BarChart3, Download, Presentation } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { API_CONFIG } from "@/lib/constants";

interface ResponseViewerProps {
  response: string | null;
  isLoading?: boolean;
  qualityScore?: number;
  sources?: string[];
}

// Extract download link from response if present
function extractDownloadInfo(response: string | null): {
  filename: string | null;
  cleanedResponse: string;
} {
  if (!response) return { filename: null, cleanedResponse: "" };

  const downloadRegex = /\[DOWNLOAD_PPTX:([^\]]+)\]/;
  const match = response.match(downloadRegex);

  if (match) {
    return {
      filename: match[1],
      cleanedResponse: response.replace(downloadRegex, ""),
    };
  }

  return { filename: null, cleanedResponse: response };
}

export function ResponseViewer({
  response,
  isLoading = false,
  qualityScore,
  sources,
}: ResponseViewerProps) {
  const { filename, cleanedResponse } = useMemo(
    () => extractDownloadInfo(response),
    [response]
  );

  const downloadUrl = filename
    ? `${API_CONFIG.baseUrl}/api/download/${filename}`
    : null;

  const isPresentationResponse = response?.includes("Presentation Ready for Download") ||
    response?.includes("Design Enhancement Tips");

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
              {isPresentationResponse ? (
                <Presentation className="h-4 w-4" />
              ) : (
                <FileText className="h-4 w-4" />
              )}
              {isPresentationResponse ? "Presentation Generated" : "Research Response"}
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

        <CardContent className="p-0 flex flex-col max-h-[600px]">
          {/* Download button section */}
          {downloadUrl && (
            <div className="flex-shrink-0 px-5 py-4 border-b bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/50">
                    <Presentation className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">PowerPoint Ready</p>
                    <p className="text-xs text-muted-foreground">
                      {filename} • Expires in 1 hour
                    </p>
                  </div>
                </div>
                <Button asChild size="sm" className="gap-2">
                  <a href={downloadUrl} download={filename}>
                    <Download className="h-4 w-4" />
                    Download
                  </a>
                </Button>
              </div>
            </div>
          )}

          <div className="flex-1 min-h-0 overflow-y-auto">
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
                {cleanedResponse || ""}
              </ReactMarkdown>
            </div>
          </div>

          {sources && sources.length > 0 && (
            <div className="flex-shrink-0 px-5 py-3 border-t bg-secondary">
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
