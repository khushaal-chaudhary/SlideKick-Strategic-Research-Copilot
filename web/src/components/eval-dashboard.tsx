"use client";

import { useEffect, useState } from "react";
import { API_CONFIG } from "@/lib/constants";
import fallbackResults from "@/data/eval-results.json";
import {
  ChevronDown,
  ChevronUp,
  Target,
  Crosshair,
  ListChecks,
  Sparkles,
  Scale,
  RefreshCw,
  Clock,
  Layers,
} from "lucide-react";

interface QueryScores {
  faithfulness: number | null;
  context_precision: number | null;
  fact_recall: number;
  answer_quality: number;
  quality_dimensions?: Record<string, number>;
}

interface PerQuery {
  id: string;
  query: string;
  query_type?: string;
  answer_preview?: string;
  scores?: QueryScores;
  agent?: {
    self_quality_score: number | null;
    iterations: number | null;
    retrieval_strategy: string | null;
    output_format: string | null;
    n_contexts: number;
  };
  judge_reasoning?: string;
  latency_s?: number;
  error?: string;
}

interface EvalResults {
  run_date: string;
  timestamp: string;
  judge_model: string;
  agent_provider: string;
  n_queries: number;
  n_scored: number;
  n_errors: number;
  aggregate: {
    faithfulness: number | null;
    context_precision: number | null;
    fact_recall: number | null;
    answer_quality: number | null;
    critic_calibration_pearson: number | null;
    avg_agent_self_score: number | null;
    avg_iterations: number | null;
    avg_latency_s: number | null;
  };
  per_query: PerQuery[];
}

const METRIC_INFO: {
  key: keyof EvalResults["aggregate"];
  label: string;
  icon: typeof Target;
  description: string;
}[] = [
  {
    key: "faithfulness",
    label: "Faithfulness",
    icon: Target,
    description: "Are the answer's claims grounded in retrieved context? (ragas, LLM judge)",
  },
  {
    key: "context_precision",
    label: "Context Precision",
    icon: Crosshair,
    description: "How much of the retrieved context is actually relevant? (ragas)",
  },
  {
    key: "fact_recall",
    label: "Fact Recall",
    icon: ListChecks,
    description: "Fraction of expected golden facts covered by the answer",
  },
  {
    key: "answer_quality",
    label: "Answer Quality",
    icon: Sparkles,
    description: "Rubric-scored relevance, completeness, specificity, coherence",
  },
];

function scoreColor(v: number): string {
  if (v >= 0.8) return "bg-emerald-500";
  if (v >= 0.6) return "bg-amber-500";
  return "bg-red-500";
}

function scoreTextColor(v: number): string {
  if (v >= 0.8) return "text-emerald-500";
  if (v >= 0.6) return "text-amber-500";
  return "text-red-500";
}

function ScoreBar({ value }: { value: number | null | undefined }) {
  if (value === null || value === undefined) {
    return <span className="text-xs text-muted-foreground">n/a</span>;
  }
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full ${scoreColor(value)}`}
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="text-xs tabular-nums w-8">{value.toFixed(2)}</span>
    </div>
  );
}

function MetricCard({
  label,
  icon: Icon,
  description,
  value,
}: {
  label: string;
  icon: typeof Target;
  description: string;
  value: number | null;
}) {
  return (
    <div className="rounded-xl border border-border/60 bg-card p-5">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Icon className="h-4 w-4" />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="mt-3 flex items-end justify-between">
        <span
          className={`text-3xl font-semibold tabular-nums ${
            value !== null ? scoreTextColor(value) : "text-muted-foreground"
          }`}
        >
          {value !== null ? value.toFixed(2) : "—"}
        </span>
        <span className="text-xs text-muted-foreground">/ 1.00</span>
      </div>
      <div className="mt-3 h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            value !== null ? scoreColor(value) : ""
          }`}
          style={{ width: value !== null ? `${Math.round(value * 100)}%` : 0 }}
        />
      </div>
      <p className="mt-3 text-xs text-muted-foreground leading-relaxed">{description}</p>
    </div>
  );
}

function QueryRow({ q }: { q: PerQuery }) {
  const [open, setOpen] = useState(false);
  if (q.error) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3">
        <p className="text-sm font-medium">{q.query}</p>
        <p className="mt-1 text-xs text-red-500">Error: {q.error}</p>
      </div>
    );
  }
  const s = q.scores;
  return (
    <div className="rounded-lg border border-border/60 bg-card">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left"
      >
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{q.query}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {q.query_type} · {q.agent?.retrieval_strategy ?? "?"} ·{" "}
            {q.latency_s?.toFixed(0)}s
          </p>
        </div>
        <div className="hidden md:flex items-center gap-4 shrink-0">
          <ScoreBar value={s?.faithfulness} />
          <ScoreBar value={s?.fact_recall} />
          <ScoreBar value={s?.answer_quality} />
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        )}
      </button>
      {open && (
        <div className="border-t border-border/60 px-4 py-3 space-y-3">
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 sm:grid-cols-4">
            <LabeledScore label="Faithfulness" value={s?.faithfulness} />
            <LabeledScore label="Context precision" value={s?.context_precision} />
            <LabeledScore label="Fact recall" value={s?.fact_recall} />
            <LabeledScore label="Answer quality" value={s?.answer_quality} />
            <LabeledScore
              label="Agent self-score"
              value={q.agent?.self_quality_score}
            />
            <div>
              <p className="text-xs text-muted-foreground">Iterations</p>
              <p className="text-sm tabular-nums">{q.agent?.iterations ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Contexts retrieved</p>
              <p className="text-sm tabular-nums">{q.agent?.n_contexts ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Output format</p>
              <p className="text-sm">{q.agent?.output_format ?? "—"}</p>
            </div>
          </div>
          {q.answer_preview && (
            <div>
              <p className="text-xs font-medium text-muted-foreground">Answer preview</p>
              <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                {q.answer_preview}…
              </p>
            </div>
          )}
          {q.judge_reasoning && (
            <div>
              <p className="text-xs font-medium text-muted-foreground">Judge reasoning</p>
              <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                {q.judge_reasoning}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function LabeledScore({
  label,
  value,
}: {
  label: string;
  value: number | null | undefined;
}) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p
        className={`text-sm font-medium tabular-nums ${
          value !== null && value !== undefined ? scoreTextColor(value) : ""
        }`}
      >
        {value !== null && value !== undefined ? value.toFixed(2) : "—"}
      </p>
    </div>
  );
}

export function EvalDashboard() {
  const [results, setResults] = useState<EvalResults>(
    fallbackResults as unknown as EvalResults
  );
  const [live, setLive] = useState(false);

  useEffect(() => {
    fetch(`${API_CONFIG.baseUrl}/api/evals/latest`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data: EvalResults) => {
        if (data?.aggregate) {
          setResults(data);
          setLive(true);
        }
      })
      .catch(() => {
        // keep bundled fallback
      });
  }, []);

  const agg = results.aggregate;
  const calibration = agg.critic_calibration_pearson;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
        <span>
          Run: <span className="text-foreground">{results.run_date}</span>
        </span>
        <span>
          Judge: <span className="text-foreground">{results.judge_model}</span>
        </span>
        <span>
          Agent LLM: <span className="text-foreground">{results.agent_provider}</span>
        </span>
        <span>
          {results.n_scored}/{results.n_queries} queries scored
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            live
              ? "bg-emerald-500/10 text-emerald-500"
              : "bg-muted text-muted-foreground"
          }`}
        >
          {live ? "live from API" : "bundled snapshot"}
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {METRIC_INFO.map((m) => (
          <MetricCard
            key={m.key}
            label={m.label}
            icon={m.icon}
            description={m.description}
            value={agg[m.key]}
          />
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-border/60 bg-card p-5">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Scale className="h-4 w-4" />
            <span className="text-sm font-medium">Critic Calibration</span>
          </div>
          <p className="mt-3 text-3xl font-semibold tabular-nums">
            {calibration !== null ? calibration.toFixed(2) : "—"}
          </p>
          <p className="mt-3 text-xs text-muted-foreground leading-relaxed">
            Pearson correlation between the agent critic&apos;s own quality score and
            the external judge. Higher means the agent knows when its own answers are
            good.
          </p>
        </div>
        <StatCard
          icon={Sparkles}
          label="Avg Self-Score"
          value={agg.avg_agent_self_score?.toFixed(2) ?? "—"}
          hint="Agent critic's average confidence"
        />
        <StatCard
          icon={RefreshCw}
          label="Avg Iterations"
          value={agg.avg_iterations?.toFixed(1) ?? "—"}
          hint="Self-reflection loops per query"
        />
        <StatCard
          icon={Clock}
          label="Avg Latency"
          value={agg.avg_latency_s ? `${agg.avg_latency_s.toFixed(0)}s` : "—"}
          hint="End-to-end per research query"
        />
      </div>

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <Layers className="h-5 w-5 text-muted-foreground" />
            Per-Query Results
          </h2>
          <div className="hidden md:flex items-center gap-4 pr-12 text-xs text-muted-foreground">
            <span className="w-[104px]">Faithfulness</span>
            <span className="w-[104px]">Fact recall</span>
            <span className="w-[104px]">Quality</span>
          </div>
        </div>
        <div className="space-y-2">
          {results.per_query.map((q) => (
            <QueryRow key={q.id} q={q} />
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: typeof Target;
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="rounded-xl border border-border/60 bg-card p-5">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Icon className="h-4 w-4" />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <p className="mt-3 text-3xl font-semibold tabular-nums">{value}</p>
      <p className="mt-3 text-xs text-muted-foreground leading-relaxed">{hint}</p>
    </div>
  );
}
