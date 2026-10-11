"use client";

import { motion } from "framer-motion";
import { CASHFLOW_BOUNDS, LEVERAGE_BOUNDS, pct, tierColor, times, TIERS } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Position of a ratio along six equal-width tier segments (left = stronger). */
export function ladderPosition(kind: "leverage" | "cashflow", value: number | null, tier: number | null): number | null {
  if (tier === null) return null;
  if (value === null) return tier === 0 ? 0.03 : tier === 5 ? 0.97 : (tier + 0.5) / 6;
  let lo: number, hi: number, frac: number;
  if (kind === "leverage") {
    const edges = [0, ...LEVERAGE_BOUNDS, 8];
    lo = edges[tier];
    hi = edges[tier + 1];
    frac = Math.min(1, Math.max(0, (value - lo) / (hi - lo)));
  } else {
    const edges = [1.2, ...CASHFLOW_BOUNDS, 0];
    lo = edges[tier];
    hi = edges[tier + 1];
    frac = Math.min(1, Math.max(0, (lo - value) / (lo - hi)));
  }
  return (tier + Math.min(0.96, Math.max(0.04, frac))) / 6;
}

export function TierLadder({ label, value, tier, kind, ghost, compact }: {
  label: string;
  value: number | null;
  tier: number | null;
  kind: "leverage" | "cashflow";
  ghost?: { value: number | null; tier: number | null } | null;
  compact?: boolean;
}) {
  const pos = ladderPosition(kind, value, tier);
  const gpos = ghost ? ladderPosition(kind, ghost.value, ghost.tier) : null;
  const fmt = (v: number | null) => (kind === "leverage" ? times(v) : pct(v, 0));
  const edges = kind === "leverage" ? LEVERAGE_BOUNDS.map((b) => `${b}x`) : CASHFLOW_BOUNDS.map((b) => `${Math.round(b * 100)}%`);
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <span className="text-[12.5px] text-ink-2">{label}</span>
        <span className="num text-[13px] font-medium text-ink-1">
          {tier === 0 && (value === 0 || value === null) ? "net cash" : fmt(value)}
          {tier !== null && <span className="ml-2 text-[11px]" style={{ color: tierColor(tier) }}>{TIERS[tier]}</span>}
        </span>
      </div>
      <div className="relative">
        <div className="flex h-2.5 gap-[3px]">
          {TIERS.map((_, i) => (
            <div key={i} className="flex-1 rounded-[3px]"
              style={{ background: tierColor(i), opacity: tier === null ? 0.18 : i === tier ? 0.95 : 0.22 }} />
          ))}
        </div>
        {gpos !== null && (
          <div className="absolute -top-1 h-[18px] w-[3px] -translate-x-1/2 rounded-full border border-ink-3 bg-transparent" style={{ left: `${gpos * 100}%` }} />
        )}
        {pos !== null && (
          <motion.div
            initial={false}
            animate={{ left: `${pos * 100}%` }}
            transition={{ type: "spring", stiffness: 220, damping: 26 }}
            className="absolute -top-1.5 h-[22px] w-[4px] -translate-x-1/2 rounded-full bg-ink-1 shadow-[0_0_0_2px_var(--panel)]"
          />
        )}
      </div>
      {!compact && (
        <div className="relative mt-1.5 h-3">
          {edges.map((e, i) => (
            <span key={e} className={cn("num absolute -translate-x-1/2 text-[9.5px] text-ink-3")} style={{ left: `${((i + 1) / 6) * 100}%` }}>{e}</span>
          ))}
        </div>
      )}
    </div>
  );
}
