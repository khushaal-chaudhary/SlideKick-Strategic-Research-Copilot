import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { EvalDashboard } from "@/components/eval-dashboard";

export const metadata: Metadata = {
  title: "Quality Metrics | SlideKick",
  description:
    "Live evaluation metrics for the SlideKick research agent: faithfulness, context precision, fact recall, answer quality, and critic calibration.",
};

export default function MetricsPage() {
  return (
    <main className="container py-10">
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to research
        </Link>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight">
          Quality Metrics
        </h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Every eval run pushes the agent through a golden dataset of research
          queries, scores the answers with an independent LLM judge (Gemini, a
          different model family than the agent&apos;s Llama), and checks whether
          the agent&apos;s self-critique agrees with the external judge.
        </p>
      </div>
      <EvalDashboard />
    </main>
  );
}
