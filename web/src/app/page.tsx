"use client";

import { Header } from "@/components/header";
import { Hero } from "@/components/hero";
import { QueryInput } from "@/components/query-input";
import { LogViewer } from "@/components/log-viewer";
import { ResponseViewer } from "@/components/response-viewer";
import { TechStack } from "@/components/tech-stack";
import { FutureIterations } from "@/components/future-iterations";
import { Footer } from "@/components/footer";
import { useResearch } from "@/hooks/use-research";
import { motion } from "framer-motion";

export default function Home() {
  const {
    isLoading,
    events,
    response,
    qualityScore,
    sources,
    submitQuery,
  } = useResearch();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <Hero />

        {/* Research Interface */}
        <section className="py-8 sm:py-12 border-t border-border/40">
          <div className="container">
            <QueryInput onSubmit={submitQuery} isLoading={isLoading} />

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
                  {response && (
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
