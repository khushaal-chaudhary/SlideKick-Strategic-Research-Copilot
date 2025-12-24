"use client";

import Link from "next/link";
import { PERSONAL_INFO, SITE_CONFIG } from "@/lib/constants";
import { Github, Linkedin, Mail, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusIndicator } from "@/components/status-indicator";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-semibold text-sm">
              SK
            </div>
            <span className="font-semibold text-lg tracking-tight">
              {SITE_CONFIG.name}
            </span>
          </div>
          <StatusIndicator />
        </div>

        <nav className="flex items-center gap-1">
          <Button variant="ghost" size="sm" asChild>
            <Link
              href={PERSONAL_INFO.website}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5"
            >
              <ExternalLink className="h-4 w-4" />
              <span className="hidden sm:inline">{PERSONAL_INFO.name}</span>
            </Link>
          </Button>
          <Button variant="ghost" size="icon" asChild>
            <Link
              href={PERSONAL_INFO.github}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub"
            >
              <Github className="h-4 w-4" />
            </Link>
          </Button>
          <Button variant="ghost" size="icon" asChild>
            <Link
              href={PERSONAL_INFO.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="LinkedIn"
            >
              <Linkedin className="h-4 w-4" />
            </Link>
          </Button>
          <Button variant="ghost" size="icon" asChild>
            <Link href={`mailto:${PERSONAL_INFO.email}`} aria-label="Email">
              <Mail className="h-4 w-4" />
            </Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}
