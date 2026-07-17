import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Header } from "@/components/header";
import { WikiContent } from "@/components/wiki-content";

export const metadata: Metadata = {
  title: "Tech Wiki | SlideKick",
  description:
    "How SlideKick works and why it's built this way: the LangGraph agent, knowledge graph, hybrid retrieval, evals, BYOD ingestion, streaming, and free-tier infrastructure decisions.",
};

export default function WikiPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container max-w-4xl py-10">
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to research
          </Link>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight">
            Tech Wiki
          </h1>
          <p className="mt-2 max-w-2xl text-muted-foreground">
            Every technical decision in this project, explained: what was
            chosen, what was rejected, and why. If you have a question after
            trying the demo, it&apos;s probably answered here.
          </p>
        </div>
        <WikiContent />
      </main>
    </div>
  );
}
