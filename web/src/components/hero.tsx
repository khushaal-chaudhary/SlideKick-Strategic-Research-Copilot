"use client";

import { SITE_CONFIG, AGENT_NODES } from "@/lib/constants";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";

export function Hero() {
  return (
    <section className="relative overflow-hidden py-20 sm:py-28">
      {/* Background gradient */}
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(45%_40%_at_50%_60%,rgba(0,0,0,0.02)_0%,transparent_100%)]" />

      <div className="container">
        <div className="mx-auto max-w-3xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Badge variant="secondary" className="mb-4">
              {SITE_CONFIG.tagline}
            </Badge>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl"
          >
            {SITE_CONFIG.name} <span className="inline-block animate-bounce">⚡</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-6 text-lg text-muted-foreground sm:text-xl max-w-2xl mx-auto"
          >
            {SITE_CONFIG.description}
          </motion.p>

          {/* Agent flow visualization */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-12 flex flex-wrap items-center justify-center gap-2"
          >
            {AGENT_NODES.map((node, index) => (
              <div key={node.id} className="flex items-center">
                <div className="flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1.5 text-sm">
                  <span>{node.emoji}</span>
                  <span className="font-medium">{node.name}</span>
                </div>
                {index < AGENT_NODES.length - 1 && (
                  <div className="mx-1 text-muted-foreground/40">
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 20 20"
                      fill="none"
                      className="text-muted-foreground/40"
                    >
                      <path
                        d="M7 10h6m0 0l-3-3m3 3l-3 3"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </motion.div>

          {/* Knowledge graph note */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="mt-8 text-sm text-muted-foreground"
          >
            Currently loaded with{" "}
            <span className="font-medium text-foreground">
              Microsoft Shareholder Letters (2020-2024)
            </span>
            {" "}— clone the repo to kick your own data!
          </motion.p>
        </div>
      </div>
    </section>
  );
}
