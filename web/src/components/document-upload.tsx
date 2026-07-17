"use client";

import { useCallback, useRef, useState, DragEvent } from "react";
import {
  CheckCircle2,
  FileText,
  FileUp,
  Loader2,
  Trash2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ErrorBanner } from "@/components/error-banner";
import type { useIngestion } from "@/hooks/use-ingestion";

const STAGE_LABELS: Record<string, string> = {
  uploading: "Uploading",
  parsing: "Parsing document",
  chunked: "Splitting into chunks",
  extracting: "Extracting entities",
  graph_write: "Building knowledge graph",
  embedding: "Embedding chunks",
  complete: "Done",
};

interface DocumentUploadProps {
  ingestion: ReturnType<typeof useIngestion>;
  disabled?: boolean;
}

export function DocumentUpload({ ingestion, disabled = false }: DocumentUploadProps) {
  const {
    isUploading,
    progress,
    stats,
    error,
    hasDocuments,
    upload,
    removeDocuments,
    clearError,
  } = ingestion;

  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (file && !isUploading && !disabled) {
        upload(file);
      }
    },
    [upload, isUploading, disabled]
  );

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      handleFile(e.dataTransfer.files?.[0]);
    },
    [handleFile]
  );

  const extractionPercent =
    progress?.stage === "extracting" && progress.total
      ? Math.round(((progress.done ?? 0) / progress.total) * 100)
      : null;

  return (
    <div className="w-full max-w-3xl mx-auto mt-6">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !isUploading && !disabled && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !isUploading && !disabled) {
            inputRef.current?.click();
          }
        }}
        className={`rounded-xl border border-dashed px-4 py-3 transition-colors cursor-pointer ${
          isDragging
            ? "border-primary bg-primary/5"
            : "border-border/60 hover:border-primary/40 hover:bg-secondary/40"
        } ${isUploading || disabled ? "cursor-not-allowed opacity-80" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt,.md"
          className="hidden"
          onChange={(e) => {
            handleFile(e.target.files?.[0]);
            e.target.value = "";
          }}
        />

        {isUploading && progress ? (
          <div className="flex items-center gap-3 text-sm">
            <Loader2 className="h-4 w-4 animate-spin text-primary shrink-0" />
            <div className="min-w-0 flex-1">
              <span className="font-medium">
                {STAGE_LABELS[progress.stage] || progress.stage}
                {extractionPercent !== null && ` — ${extractionPercent}%`}
              </span>
              <p className="text-xs text-muted-foreground truncate">
                {progress.message}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <FileUp className="h-4 w-4 shrink-0" />
            <span>
              <span className="font-medium text-foreground">
                Bring your own docs
              </span>{" "}
              — drop a PDF, TXT, or MD file (max 10 MB) to research it alongside
              the demo corpus
            </span>
          </div>
        )}
      </div>

      <AnimatePresence>
        {!isUploading && progress?.stage === "complete" && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-2 flex items-center gap-2 text-xs text-muted-foreground"
          >
            <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
            {progress.message}
          </motion.div>
        )}
      </AnimatePresence>

      {hasDocuments && stats && (
        <div className="mt-3 flex items-center justify-between gap-2 rounded-lg bg-secondary/60 px-3 py-2 text-xs">
          <div className="flex items-center gap-2 min-w-0 text-muted-foreground">
            <FileText className="h-3.5 w-3.5 shrink-0 text-primary" />
            <span className="truncate">
              <span className="font-medium text-foreground">
                {stats.documents.join(", ")}
              </span>{" "}
              in your workspace ({stats.entities} entities, {stats.chunks}{" "}
              chunks) — included in research
            </span>
          </div>
          <button
            type="button"
            onClick={removeDocuments}
            disabled={isUploading}
            className="flex items-center gap-1 shrink-0 rounded-md px-2 py-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50"
            title="Remove your documents"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Remove
          </button>
        </div>
      )}

      {error && (
        <div className="mt-3">
          <ErrorBanner error={error} onDismiss={clearError} />
        </div>
      )}
    </div>
  );
}
