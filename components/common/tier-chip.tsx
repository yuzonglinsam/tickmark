import { TIERS, tierColor } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Indicative financial-risk tier. Colour is never the only cue: the label is always shown. */
export function TierChip({ tier, compact = false, className }: { tier: number | null | undefined; compact?: boolean; className?: string }) {
  if (tier === null || tier === undefined) {
    return (
      <span className={cn("inline-flex items-center rounded-full border border-hairline-strong px-2 py-0.5 text-[10.5px] text-ink-3", className)}>
        {compact ? "N.M." : "Not meaningful"}
      </span>
    );
  }
  const label = TIERS[tier];
  return (
    <span
      className={cn("inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-[10.5px] font-medium", className)}
      style={{ color: tierColor(tier), background: `color-mix(in oklab, ${tierColor(tier)} 14%, transparent)`, border: `1px solid color-mix(in oklab, ${tierColor(tier)} 35%, transparent)` }}
    >
      <TierPips tier={tier} />
      {compact && label === "Highly leveraged" ? "Highly lev." : label}
    </span>
  );
}

export function TierPips({ tier }: { tier: number }) {
  return (
    <span className="inline-flex items-end gap-[2px]" aria-hidden>
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <span
          key={i}
          className="w-[3px] rounded-[1px]"
          style={{ height: 4 + i * 1.2, background: i <= tier ? "currentColor" : "color-mix(in oklab, currentColor 25%, transparent)" }}
        />
      ))}
    </span>
  );
}
