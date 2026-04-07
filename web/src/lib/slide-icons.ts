/**
 * Category → Lucide icon mapping for slide layouts.
 *
 * The LLM outputs a semantic category string; this module maps it
 * to a concrete icon. No hallucinated icon names, no missing assets.
 */

import {
  TrendingUp,
  DollarSign,
  AlertTriangle,
  Rocket,
  Compass,
  Cpu,
  ArrowUpRight,
  Target,
  Users,
  Lightbulb,
  Shield,
  BarChart3,
  type LucideIcon,
} from "lucide-react";

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  financial_metric: BarChart3,
  revenue: DollarSign,
  risk: AlertTriangle,
  opportunity: Rocket,
  strategy: Compass,
  technology: Cpu,
  growth: ArrowUpRight,
  competition: Target,
  leadership: Users,
  profitability: TrendingUp,
  valuation: DollarSign,
  security: Shield,
};

export function getIconForCategory(category: string): LucideIcon {
  return CATEGORY_ICONS[category] ?? Lightbulb;
}
