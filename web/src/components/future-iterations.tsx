"use client";

import { FUTURE_ITERATIONS } from "@/lib/constants";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { Rocket, Lightbulb } from "lucide-react";

const statusConfig: Record<
  string,
  { label: string; variant: "default" | "secondary" | "outline" }
> = {
  planned: { label: "Planned", variant: "default" },
  idea: { label: "Idea", variant: "outline" },
  done: { label: "Done", variant: "secondary" },
};

export function FutureIterations() {
  return (
    <section className="py-16 sm:py-20 bg-secondary/30">
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Future Iterations
          </h2>
          <p className="mt-3 text-muted-foreground max-w-xl mx-auto">
            Planned enhancements and ideas for expanding the platform
            capabilities.
          </p>
        </motion.div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 max-w-4xl mx-auto">
          {FUTURE_ITERATIONS.map((item, index) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <Card className="h-full border-border/50 bg-background">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary">
                      {item.status === "planned" ? (
                        <Rocket className="h-4 w-4" />
                      ) : (
                        <Lightbulb className="h-4 w-4" />
                      )}
                    </div>
                    <Badge variant={statusConfig[item.status]?.variant || "outline"}>
                      {statusConfig[item.status]?.label || item.status}
                    </Badge>
                  </div>
                  <h3 className="mt-3 font-semibold">{item.title}</h3>
                  <p className="mt-1.5 text-sm text-muted-foreground leading-relaxed">
                    {item.description}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
