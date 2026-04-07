/**
 * Slide presentation themes.
 *
 * Each theme is a complete set of CSS custom properties applied to the
 * Reveal.js container. The LLM picks a theme *name*; all color decisions
 * are made here, not by the model.
 */

export interface SlideTheme {
  /** Primary background */
  bg: string;
  /** Slightly lighter surface for cards / stat boxes */
  surface: string;
  /** Accent color for highlights, deltas, icons */
  accent: string;
  /** Primary text */
  text: string;
  /** Secondary / muted text */
  muted: string;
  /** Subtle border color */
  border: string;
  /** Positive delta color */
  positive: string;
  /** Negative delta color */
  negative: string;
}

export const THEMES: Record<string, SlideTheme> = {
  slate: {
    bg: "#0f172a",
    surface: "#1e293b",
    accent: "#3b82f6",
    text: "#f8fafc",
    muted: "#94a3b8",
    border: "#334155",
    positive: "#34d399",
    negative: "#f87171",
  },
  growth: {
    bg: "#052e16",
    surface: "#14532d",
    accent: "#eab308",
    text: "#f0fdf4",
    muted: "#86efac",
    border: "#166534",
    positive: "#4ade80",
    negative: "#fca5a5",
  },
  clarity: {
    bg: "#ffffff",
    surface: "#f1f5f9",
    accent: "#2563eb",
    text: "#0f172a",
    muted: "#64748b",
    border: "#e2e8f0",
    positive: "#16a34a",
    negative: "#dc2626",
  },
  bold: {
    bg: "#09090b",
    surface: "#18181b",
    accent: "#facc15",
    text: "#fafafa",
    muted: "#a1a1aa",
    border: "#27272a",
    positive: "#4ade80",
    negative: "#f87171",
  },
  warm: {
    bg: "#faf5f0",
    surface: "#f5ebe0",
    accent: "#c2410c",
    text: "#1c1917",
    muted: "#78716c",
    border: "#d6d3d1",
    positive: "#16a34a",
    negative: "#dc2626",
  },
};

export function getTheme(name: string): SlideTheme {
  return THEMES[name] ?? THEMES.slate;
}

/** Convert a theme to a CSS variables style object for inline application. */
export function themeToCSS(theme: SlideTheme): Record<string, string> {
  return {
    "--slide-bg": theme.bg,
    "--slide-surface": theme.surface,
    "--slide-accent": theme.accent,
    "--slide-text": theme.text,
    "--slide-muted": theme.muted,
    "--slide-border": theme.border,
    "--slide-positive": theme.positive,
    "--slide-negative": theme.negative,
  };
}
