import { cn } from "@/lib/utils";

/** Tickmark logo: an auditor's tick mark — "agreed to source". */
export function LogoMark({ className, animated = false }: { className?: string; animated?: boolean }) {
  return (
    <svg viewBox="0 0 32 32" className={cn("size-7", animated && "tick-draw", className)} aria-hidden="true">
      <rect x="1" y="1" width="30" height="30" rx="8" fill="#16110a" stroke="var(--amber)" strokeOpacity="0.55" />
      <path d="M8.5 16.5 L13.5 21.5 L23.5 10.5" fill="none" stroke="var(--amber)" strokeWidth="3"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <LogoMark />
      <span className="text-[17px] font-semibold tracking-tight text-ink-1">
        tick<span className="text-amber">mark</span>
      </span>
    </span>
  );
}
