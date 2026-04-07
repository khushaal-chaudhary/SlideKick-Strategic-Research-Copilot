"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import {
  Maximize2,
  Minimize2,
  Presentation,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { getTheme, themeToCSS, type SlideTheme } from "@/lib/slide-themes";
import { getIconForCategory } from "@/lib/slide-icons";

// ─── Types ───────────────────────────────────────────────────────────────────

interface StatItem {
  value: string;
  label: string;
  delta?: string;
}

interface BulletItem {
  heading: string;
  detail: string;
}

interface TimelineEvent {
  date: string;
  label: string;
}

interface ActionItem {
  heading: string;
  detail: string;
}

interface SlideData {
  layout: string;
  content: Record<string, unknown>;
  speaker_notes?: string;
}

export interface SlidesPayload {
  theme?: string;
  title: string;
  subtitle?: string;
  slides: SlideData[];
}

interface PresentationViewerProps {
  slides: SlidesPayload;
  qualityScore?: number;
}

// ─── Layout Components ───────────────────────────────────────────────────────

function TitleSlide({
  content,
  theme,
}: {
  content: Record<string, unknown>;
  theme: SlideTheme;
}) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-12 text-center">
      <h1
        className="text-5xl md:text-7xl font-bold leading-tight mb-6"
        style={{ color: theme.text }}
      >
        {content.headline as string}
      </h1>
      {content.subtitle ? (
        <p
          className="text-xl md:text-2xl font-light"
          style={{ color: theme.muted }}
        >
          {String(content.subtitle)}
        </p>
      ) : null}
      <div
        className="w-24 h-1 mt-8 rounded-full"
        style={{ backgroundColor: theme.accent }}
      />
    </div>
  );
}

function StatTrioSlide({
  content,
  theme,
}: {
  content: Record<string, unknown>;
  theme: SlideTheme;
}) {
  const stats = (content.stats as StatItem[]) ?? [];
  return (
    <div className="flex flex-col h-full px-12 py-10">
      <h2
        className="text-3xl md:text-4xl font-bold mb-12"
        style={{ color: theme.text }}
      >
        {content.title as string}
      </h2>
      <div className="flex-1 grid grid-cols-3 gap-8 items-center">
        {stats.slice(0, 3).map((stat, i) => (
          <div
            key={i}
            className="flex flex-col items-center p-8 rounded-2xl text-center"
            style={{ backgroundColor: theme.surface, border: `1px solid ${theme.border}` }}
          >
            <span
              className="text-5xl md:text-6xl font-bold mb-3"
              style={{ color: theme.accent }}
            >
              {stat.value}
            </span>
            <span
              className="text-lg font-medium mb-2"
              style={{ color: theme.text }}
            >
              {stat.label}
            </span>
            {stat.delta && (
              <span
                className="text-sm font-semibold px-3 py-1 rounded-full"
                style={{
                  color: stat.delta.startsWith("-")
                    ? theme.negative
                    : theme.positive,
                  backgroundColor: stat.delta.startsWith("-")
                    ? theme.negative + "18"
                    : theme.positive + "18",
                }}
              >
                {stat.delta}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function BulletsSlide({
  content,
  theme,
}: {
  content: Record<string, unknown>;
  theme: SlideTheme;
}) {
  const bullets = (content.bullets as BulletItem[]) ?? [];
  const category = (content.category as string) ?? "strategy";
  const Icon = getIconForCategory(category);

  return (
    <div className="flex flex-col h-full px-12 py-10">
      <div className="flex items-center gap-4 mb-10">
        <div
          className="p-3 rounded-xl"
          style={{ backgroundColor: theme.accent + "20" }}
        >
          <Icon className="w-7 h-7" style={{ color: theme.accent }} />
        </div>
        <h2
          className="text-3xl md:text-4xl font-bold"
          style={{ color: theme.text }}
        >
          {content.title as string}
        </h2>
      </div>
      <div className="flex-1 flex flex-col justify-center gap-6">
        {bullets.slice(0, 4).map((bullet, i) => (
          <div
            key={i}
            className="flex items-start gap-5 p-5 rounded-xl"
            style={{ backgroundColor: theme.surface, border: `1px solid ${theme.border}` }}
          >
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 text-sm font-bold"
              style={{
                backgroundColor: theme.accent + "20",
                color: theme.accent,
              }}
            >
              {i + 1}
            </div>
            <div>
              <span
                className="font-semibold text-lg"
                style={{ color: theme.text }}
              >
                {bullet.heading}
              </span>
              <span
                className="text-base ml-2"
                style={{ color: theme.muted }}
              >
                {bullet.detail}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TwoColumnSlide({
  content,
  theme,
}: {
  content: Record<string, unknown>;
  theme: SlideTheme;
}) {
  const left = content.left as { label: string; points: string[] } | undefined;
  const right = content.right as { label: string; points: string[] } | undefined;

  const renderColumn = (col: { label: string; points: string[] }) => (
    <div
      className="flex flex-col p-8 rounded-2xl h-full"
      style={{ backgroundColor: theme.surface, border: `1px solid ${theme.border}` }}
    >
      <h3
        className="text-2xl font-bold mb-6 pb-4"
        style={{ color: theme.accent, borderBottom: `2px solid ${theme.border}` }}
      >
        {col.label}
      </h3>
      <div className="flex flex-col gap-4">
        {col.points?.map((point, i) => (
          <div key={i} className="flex items-start gap-3">
            <div
              className="w-2 h-2 rounded-full mt-2 flex-shrink-0"
              style={{ backgroundColor: theme.accent }}
            />
            <span className="text-base" style={{ color: theme.text }}>
              {point}
            </span>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-full px-12 py-10">
      <h2
        className="text-3xl md:text-4xl font-bold mb-10"
        style={{ color: theme.text }}
      >
        {content.title as string}
      </h2>
      <div className="flex-1 grid grid-cols-2 gap-8 items-stretch">
        {left && renderColumn(left)}
        {right && renderColumn(right)}
      </div>
    </div>
  );
}

function QuoteCalloutSlide({
  content,
  theme,
}: {
  content: Record<string, unknown>;
  theme: SlideTheme;
}) {
  const category = (content.category as string) ?? "strategy";
  const Icon = getIconForCategory(category);

  return (
    <div className="flex flex-col items-center justify-center h-full px-16 text-center">
      <div
        className="p-4 rounded-2xl mb-8"
        style={{ backgroundColor: theme.accent + "20" }}
      >
        <Icon className="w-10 h-10" style={{ color: theme.accent }} />
      </div>
      <h2
        className="text-2xl font-semibold mb-8"
        style={{ color: theme.muted }}
      >
        {content.title as string}
      </h2>
      <blockquote
        className="text-3xl md:text-4xl font-semibold leading-relaxed max-w-4xl mb-8"
        style={{ color: theme.text }}
      >
        &ldquo;{content.quote as string}&rdquo;
      </blockquote>
      {content.attribution ? (
        <p className="text-base mb-2" style={{ color: theme.accent }}>
          {String(content.attribution)}
        </p>
      ) : null}
      {content.supporting ? (
        <p className="text-sm" style={{ color: theme.muted }}>
          {String(content.supporting)}
        </p>
      ) : null}
    </div>
  );
}

function TimelineSlide({
  content,
  theme,
}: {
  content: Record<string, unknown>;
  theme: SlideTheme;
}) {
  const events = (content.events as TimelineEvent[]) ?? [];

  return (
    <div className="flex flex-col h-full px-12 py-10">
      <h2
        className="text-3xl md:text-4xl font-bold mb-12"
        style={{ color: theme.text }}
      >
        {content.title as string}
      </h2>
      <div className="flex-1 flex items-center">
        <div className="w-full relative">
          {/* Timeline line */}
          <div
            className="absolute left-0 right-0 top-1/2 h-0.5 -translate-y-1/2"
            style={{ backgroundColor: theme.border }}
          />
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${Math.min(events.length, 6)}, 1fr)` }}>
            {events.slice(0, 6).map((event, i) => (
              <div key={i} className="flex flex-col items-center text-center relative">
                {/* Dot */}
                <div
                  className="w-5 h-5 rounded-full mb-4 relative z-10"
                  style={{
                    backgroundColor: theme.accent,
                    boxShadow: `0 0 0 4px ${theme.accent}30`,
                  }}
                />
                {/* Date */}
                <span
                  className="text-lg font-bold mb-2"
                  style={{ color: theme.accent }}
                >
                  {event.date}
                </span>
                {/* Label */}
                <span
                  className="text-sm leading-snug"
                  style={{ color: theme.muted }}
                >
                  {event.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ClosingSlide({
  content,
  theme,
}: {
  content: Record<string, unknown>;
  theme: SlideTheme;
}) {
  const actions = (content.actions as ActionItem[]) ?? [];

  return (
    <div className="flex flex-col h-full px-12 py-10">
      <h2
        className="text-3xl md:text-4xl font-bold mb-12"
        style={{ color: theme.text }}
      >
        {content.title as string}
      </h2>
      <div className="flex-1 flex flex-col justify-center gap-6">
        {actions.slice(0, 4).map((action, i) => (
          <div
            key={i}
            className="flex items-start gap-6 p-6 rounded-xl"
            style={{ backgroundColor: theme.surface, border: `1px solid ${theme.border}` }}
          >
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 text-xl font-bold"
              style={{
                backgroundColor: theme.accent,
                color: theme.bg,
              }}
            >
              {i + 1}
            </div>
            <div>
              <span
                className="text-xl font-bold block mb-1"
                style={{ color: theme.text }}
              >
                {action.heading}
              </span>
              <span className="text-base" style={{ color: theme.muted }}>
                {action.detail}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Layout Renderer ─────────────────────────────────────────────────────────

function SlideLayout({
  slide,
  theme,
}: {
  slide: SlideData;
  theme: SlideTheme;
}) {
  const content = slide.content;
  switch (slide.layout) {
    case "title":
      return <TitleSlide content={content} theme={theme} />;
    case "stat-trio":
      return <StatTrioSlide content={content} theme={theme} />;
    case "bullets":
      return <BulletsSlide content={content} theme={theme} />;
    case "two-column":
      return <TwoColumnSlide content={content} theme={theme} />;
    case "quote-callout":
      return <QuoteCalloutSlide content={content} theme={theme} />;
    case "timeline":
      return <TimelineSlide content={content} theme={theme} />;
    case "closing":
      return <ClosingSlide content={content} theme={theme} />;
    default:
      // Fallback: treat as bullets
      return <BulletsSlide content={content} theme={theme} />;
  }
}

// ─── Main Component ──────────────────────────────────────────────────────────

export function PresentationViewer({
  slides: payload,
  qualityScore,
}: PresentationViewerProps) {
  /* eslint-disable @typescript-eslint/no-explicit-any */
  const deckRef = useRef<HTMLDivElement>(null);
  const revealRef = useRef<any>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isReady, setIsReady] = useState(false);

  const theme = useMemo(() => getTheme(payload.theme ?? "slate"), [payload.theme]);
  const cssVars = useMemo(() => themeToCSS(theme), [theme]);
  const totalSlides = payload.slides.length;

  // Initialize Reveal.js
  useEffect(() => {
    let revealInstance: any = null;

    async function init() {
      if (!deckRef.current) return;

      const Reveal = (await import("reveal.js")).default;

      revealInstance = new Reveal(deckRef.current, {
        embedded: true,
        hash: false,
        history: false,
        controls: false, // We render our own controls
        progress: true,
        center: false,
        transition: "slide",
        transitionSpeed: "default",
        width: 1280,
        height: 720,
        margin: 0,
        minScale: 0.2,
        maxScale: 2.0,
        keyboard: true,
      });

      await revealInstance.initialize();
      revealRef.current = revealInstance;
      setIsReady(true);

      revealInstance.on("slidechanged", (event: any) => {
        setCurrentSlide(event.indexh);
      });
    }

    init();

    return () => {
      if (revealInstance) {
        try {
          revealInstance.destroy();
        } catch {
          // Reveal.js can throw on cleanup in dev
        }
      }
    };
  }, [payload]);

  // Import Reveal.js base CSS
  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://cdn.jsdelivr.net/npm/reveal.js@5/dist/reveal.css";
    link.id = "reveal-css";
    if (!document.getElementById("reveal-css")) {
      document.head.appendChild(link);
    }
    return () => {
      const el = document.getElementById("reveal-css");
      if (el) el.remove();
    };
  }, []);

  const toggleFullscreen = () => {
    if (!deckRef.current) return;
    const container = deckRef.current.closest("[data-presentation-root]") as HTMLElement;
    if (!container) return;

    if (!document.fullscreenElement) {
      container.requestFullscreen().then(() => setIsFullscreen(true));
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false));
    }
  };

  // Listen for fullscreen exit via Escape
  useEffect(() => {
    const handler = () => {
      if (!document.fullscreenElement) setIsFullscreen(false);
    };
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  const goTo = (index: number) => {
    if (revealRef.current) revealRef.current.slide(index);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="border-border/50 shadow-subtle overflow-hidden">
        {/* Header */}
        <CardHeader className="py-3 px-5 border-b">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Presentation className="h-4 w-4" />
              Presentation
              <Badge variant="secondary" className="ml-2 text-xs">
                {totalSlides} slides
              </Badge>
              {payload.theme && (
                <Badge variant="outline" className="text-xs capitalize">
                  {payload.theme}
                </Badge>
              )}
            </CardTitle>
            <div className="flex items-center gap-2">
              {qualityScore !== undefined && (
                <Badge variant="secondary" className="gap-1 text-xs">
                  {Math.round(qualityScore * 100)}% quality
                </Badge>
              )}
              <Button variant="outline" size="sm" onClick={toggleFullscreen} className="gap-1.5">
                {isFullscreen ? (
                  <Minimize2 className="h-3.5 w-3.5" />
                ) : (
                  <Maximize2 className="h-3.5 w-3.5" />
                )}
                {isFullscreen ? "Exit" : "Present"}
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0" data-presentation-root>
          {/* Reveal.js container */}
          <div
            ref={deckRef}
            className="reveal"
            style={{
              ...cssVars,
              width: "100%",
              height: isFullscreen ? "100vh" : "min(540px, 56.25vw)",
              position: "relative",
            } as React.CSSProperties}
          >
            <div className="slides">
              {payload.slides.map((slide, i) => (
                <section
                  key={i}
                  style={{
                    backgroundColor: theme.bg,
                    width: "100%",
                    height: "100%",
                  }}
                >
                  <SlideLayout slide={slide} theme={theme} />
                </section>
              ))}
            </div>
          </div>

          {/* Custom navigation bar */}
          {isReady && (
            <div
              className="flex items-center justify-between px-5 py-2.5 border-t"
              style={{ backgroundColor: theme.surface, borderColor: theme.border }}
            >
              <Button
                variant="ghost"
                size="sm"
                onClick={() => goTo(currentSlide - 1)}
                disabled={currentSlide === 0}
                className="gap-1"
                style={{ color: theme.muted }}
              >
                <ChevronLeft className="h-4 w-4" />
                Prev
              </Button>

              {/* Slide indicator dots */}
              <div className="flex items-center gap-1.5">
                {payload.slides.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => goTo(i)}
                    className="w-2 h-2 rounded-full transition-all duration-200"
                    style={{
                      backgroundColor:
                        i === currentSlide ? theme.accent : theme.border,
                      transform: i === currentSlide ? "scale(1.3)" : "scale(1)",
                    }}
                  />
                ))}
              </div>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => goTo(currentSlide + 1)}
                disabled={currentSlide === totalSlides - 1}
                className="gap-1"
                style={{ color: theme.muted }}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
