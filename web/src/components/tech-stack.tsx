"use client";

import { TECH_STACK } from "@/lib/constants";
import { Card, CardContent } from "@/components/ui/card";
import { motion } from "framer-motion";
import {
  Workflow,
  Database,
  Globe,
  Server,
  TrendingUp,
  Search,
  Presentation,
  Cloud,
} from "lucide-react";

const iconMap: Record<string, React.ReactNode> = {
  workflow: <Workflow className="h-5 w-5" />,
  database: <Database className="h-5 w-5" />,
  globe: <Globe className="h-5 w-5" />,
  server: <Server className="h-5 w-5" />,
  "trending-up": <TrendingUp className="h-5 w-5" />,
  search: <Search className="h-5 w-5" />,
  presentation: <Presentation className="h-5 w-5" />,
  cloud: <Cloud className="h-5 w-5" />,
};

export function TechStack() {
  return (
    <section className="py-16 sm:py-20">
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Built with Modern Tech
          </h2>
          <p className="mt-3 text-muted-foreground max-w-xl mx-auto">
            A production-ready architecture combining knowledge graphs, LLMs,
            and real-time data sources.
          </p>
        </motion.div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {TECH_STACK.map((tech, index) => (
            <motion.div
              key={tech.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <Card className="h-full hover-lift border-border/50">
                <CardContent className="p-5">
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-secondary text-foreground">
                      {iconMap[tech.icon] || <Globe className="h-5 w-5" />}
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground uppercase tracking-wider">
                        {tech.category}
                      </div>
                      <h3 className="font-semibold">{tech.name}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {tech.description}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
