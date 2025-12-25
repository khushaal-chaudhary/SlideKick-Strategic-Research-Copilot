"use client";

import { useState, FormEvent } from "react";
import { Send, Loader2, Sparkles, Zap, Server } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { EXAMPLE_QUERIES } from "@/lib/constants";
import { motion } from "framer-motion";
import type { LLMProvider } from "@/hooks/use-research";

interface QueryInputProps {
  onSubmit: (query: string, provider: LLMProvider) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export function QueryInput({
  onSubmit,
  isLoading = false,
  disabled = false,
}: QueryInputProps) {
  const [query, setQuery] = useState("");
  const [provider, setProvider] = useState<LLMProvider>("ollama");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading && !disabled) {
      onSubmit(query.trim(), provider);
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Input
            type="text"
            placeholder="Ask a strategic research question..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading || disabled}
            className="h-14 pr-14 text-base rounded-xl shadow-subtle border-border/50 focus:border-primary/50 transition-all"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!query.trim() || isLoading || disabled}
            className="absolute right-2 top-1/2 -translate-y-1/2 h-10 w-10 rounded-lg"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </form>

      {/* Provider selector and Example queries */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.4 }}
        className="mt-4 space-y-4"
      >
        {/* LLM Provider Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>LLM Provider:</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setProvider("ollama")}
              disabled={isLoading || disabled}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all ${
                provider === "ollama"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary hover:bg-secondary/80 text-muted-foreground"
              } disabled:opacity-50`}
            >
              <Server className="h-3.5 w-3.5" />
              Ollama
              <Badge variant="outline" className="ml-1 text-[10px] px-1.5 py-0">
                Free
              </Badge>
            </button>
            <button
              type="button"
              onClick={() => setProvider("groq")}
              disabled={isLoading || disabled}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all ${
                provider === "groq"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary hover:bg-secondary/80 text-muted-foreground"
              } disabled:opacity-50`}
            >
              <Zap className="h-3.5 w-3.5" />
              Groq
              <Badge variant="outline" className="ml-1 text-[10px] px-1.5 py-0">
                Fast
              </Badge>
            </button>
          </div>
        </div>

        {/* Provider info message */}
        <p className="text-xs text-muted-foreground text-center">
          {provider === "ollama"
            ? "Using local Ollama (qwen2.5:7b) - slower but unlimited"
            : "Using Groq (llama-3.3-70b) - faster but may hit rate limits"}
        </p>

        {/* Example queries */}
        <div>
          <div className="flex items-center gap-2 mb-2 text-sm text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Try an example</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_QUERIES.slice(0, 3).map((example, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(example)}
                disabled={isLoading || disabled}
                className="text-left text-sm px-3 py-1.5 rounded-full bg-secondary hover:bg-secondary/80 transition-colors truncate max-w-full disabled:opacity-50"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
