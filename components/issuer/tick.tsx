"use client";

import { Check, Minus, Sigma } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { fact, metric } from "@/lib/issuer";
import { useIssuerCtx, type TraceTarget } from "./source-context";

type Status = "reported" | "derived" | "missing";

export function statusOf(target: TraceTarget, ctx: ReturnType<typeof useIssuerCtx>): Status {
  if (target.kind === "fact") {
    const f = fact(ctx.doc, target.period, target.key);
    if (!f || f.value === null) return "missing";
    return f.status === "reported" ? "reported" : "derived";
  }
  if (target.kind === "metric") {
    const m = metric(ctx.doc, target.period, target.key);
    return !m || m.value === null ? "missing" : "derived";
  }
  return "reported";
}

/** The tick mark: click any figure to trace it to the SEC filing it came from. */
export function Tick({ target, children, className, iconOnly = false }: {
  target: TraceTarget;
  children?: React.ReactNode;
  className?: string;
  iconOnly?: boolean;
}) {
  const ctx = useIssuerCtx();
  const status = statusOf(target, ctx);
  const Icon = status === "reported" ? Check : status === "derived" ? Sigma : Minus;
  const tip =
    status === "reported" ? "Reported in SEC XBRL — click to trace" :
    status === "derived" ? "Computed from tagged SEC facts — click for formula & sources" :
    "Not available — click for the reason";
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            ctx.trace(target);
          }}
          className={cn(
            "group/tick inline-flex items-center gap-1.5 rounded-sm text-left outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring/60",
            className,
          )}
        >
          {!iconOnly && children}
          <span
            className={cn(
              "inline-flex size-[15px] shrink-0 items-center justify-center rounded-[4px] border transition-all group-hover/tick:scale-110",
              status === "reported" && "border-amber/40 bg-amber/10 text-amber",
              status === "derived" && "border-cyan/35 bg-cyan/10 text-cyan",
              status === "missing" && "border-hairline-strong text-ink-3",
            )}
          >
            <Icon className="size-[10px]" strokeWidth={3} />
          </span>
        </button>
      </TooltipTrigger>
      <TooltipContent side="top" className="text-[11.5px]">{tip}</TooltipContent>
    </Tooltip>
  );
}
