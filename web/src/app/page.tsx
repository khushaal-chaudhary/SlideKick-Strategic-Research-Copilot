"use client";

import { Header } from "@/components/header";
import { Hero } from "@/components/hero";
import { QueryInput } from "@/components/query-input";
import { DocumentUpload } from "@/components/document-upload";
import { LogViewer } from "@/components/log-viewer";
import { ResponseViewer } from "@/components/response-viewer";
import { PresentationViewer } from "@/components/presentation-viewer";
import { TechStack } from "@/components/tech-stack";
import { FutureIterations } from "@/components/future-iterations";
import { Footer } from "@/components/footer";
import { ErrorBanner } from "@/components/error-banner";
import { useResearch } from "@/hooks/use-research";
import { useIngestion } from "@/hooks/use-ingestion";
import { getWorkspaceId } from "@/lib/workspace";
import { motion } from "framer-motion";
import type { LLMProvider } from "@/hooks/use-research";

export default function Home() {
  const {
    isLoading,
    events,
    response,
    qualityScore,
    sources,
    error,
    slidesContent,
    submitQuery,
    clearError,
  } = useResearch();

  const ingestion = useIngestion();

  const handleSubmit = (query: string, provider: LLMProvider) => {
    submitQuery(query, provider, ingestion.hasDocuments ? getWorkspaceId() : null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <Hero />

        {/* Research Interface */}
        <section className="py-8 sm:py-12 border-t border-border/40">
          <div className="container">
            <QueryInput onSubmit={handleSubmit} isLoading={isLoading} />

            {/* BYOD upload */}
            <DocumentUpload ingestion={ingestion} disabled={isLoading} />

            {/* Error Banner */}
            {error && (
              <div className="mt-6">
                <ErrorBanner error={error} onDismiss={clearError} />
              </div>
            )}

            {/* Presentation Viewer (full-width, above the grid) */}
            {slidesContent && (
              <div className="mt-8">
                <PresentationViewer
                  slides={slidesContent}
                  qualityScore={qualityScore ?? undefined}
                />
              </div>
            )}

            {/* Results Grid */}
            {(events.length > 0 || response) && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="mt-8 grid gap-6 lg:grid-cols-2"
              >
                {/* Log Viewer */}
                <div className="lg:order-2">
                  <LogViewer events={events} isActive={isLoading} />
                </div>

                {/* Response */}
                <div className="lg:order-1">
                  {response && !slidesContent && (
                    <ResponseViewer
                      response={response}
                      qualityScore={qualityScore ?? undefined}
                      sources={sources}
                    />
                  )}
                </div>
              </motion.div>
            )}
          </div>
        </section>

        {/* Tech Stack Section */}
        <TechStack />

        {/* Future Iterations Section */}
        <FutureIterations />
      </main>

      <Footer />
    </div>
  );
}
