"use client";

import { useState, FormEvent } from "react";
import { Send, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EXAMPLE_QUERIES } from "@/lib/constants";
import { motion } from "framer-motion";

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export function QueryInput({
  onSubmit,
  isLoading = false,
  disabled = false,
}: QueryInputProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading && !disabled) {
      onSubmit(query.trim());
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

      {/* Example queries */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.4 }}
        className="mt-4"
      >
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
      </motion.div>
    </div>
  );
}
