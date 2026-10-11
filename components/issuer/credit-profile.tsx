"use client";

import { Info } from "lucide-react";
import { Panel } from "@/components/common/panel";
import { TierChip } from "@/components/common/tier-chip";
import { fact, metric } from "@/lib/issuer";
import { fmtMetric, METRIC_LABELS, money, pct, times, TIERS } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useIssuerCtx } from "./source-context";
import { Tick } from "./tick";
import { TierLadder } from "./tier-ladder";

const GRID: { key: string; kind: "fact" | "metric"; peer?: string }[] = [
  { key: "revenue", kind: "fact" },
  { key: "ebitda_proxy", kind: "metric" },
  { key: "operating_margin", kind: "metric", peer: "om" },
  { key: "revenue_growth", kind: "metric", peer: "g" },
  { key: "operating_cash_flow", kind: "fact" },
  { key: "fcf", kind: "metric" },
  { key: "debt", kind: "fact" },
  { key: "cash", kind: "fact" },
  { key: "net_debt_adj", kind: "metric" },
  { key: "gross_leverage", kind: "metric", peer: "lev" },
  { key: "net_leverage_adj", kind: "metric", peer: "nlev" },
  { key: "net_leverage", kind: "metric" },
  { key: "interest_coverage", kind: "metric", peer: "icov" },
  { key: "ebitda_coverage", kind: "metric", peer: "ecov" },
  { key: "cfo_to_debt", kind: "metric", peer: "cfod" },
  { key: "fcf_to_debt", kind: "metric", peer: "fcfd" },
  { key: "current_ratio", kind: "metric", peer: "cr" },
  { key: "debt_to_capital", kind: "metric" },
];

export function CreditProfile() {
  const { doc } = useIssuerCtx();
  const rp = doc.risk_profile;
  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
        <Panel eyebrow={`Indicative financial risk profile · ${doc.primary}`} title={<span className="flex items-center gap-3">Financial risk <TierChip tier={rp.overall} className="text-[12px]" /></span>}>
          <div className="space-y-6">
            <TierLadder label="Net debt / EBITDA (net of cash & ST investments)" value={rp.leverage.value} tier={rp.leverage.tier} kind="leverage" />
            <TierLadder label="CFO / net debt (FFO/debt proxy)" value={rp.cashflow.value} tier={rp.cashflow.tier} kind="cashflow" />
            <div className="grid grid-cols-2 gap-3 text-[12px]">
              <div className="rounded-lg border border-hairline bg-panel-2 p-3">
                <div className="label-caps">Gross basis</div>
                <div className="num mt-1.5 text-ink-1">{times(rp.gross.leverage)} · {pct(rp.gross.cashflow, 0)}</div>
                <div className="mt-1 text-ink-3">Before netting cash</div>
              </div>
              <div className="rounded-lg border border-hairline bg-panel-2 p-3">
                <div className="label-caps">Net debt</div>
                <div className="num mt-1.5 text-ink-1">{money(rp.net_debt, doc.issuer.currency)}</div>
                <div className="mt-1 text-ink-3">Liquid assets {money(rp.liquid_assets)}</div>
              </div>
            </div>
            <div className="flex gap-2.5 rounded-lg border border-hairline bg-panel-2 p-3.5 text-[12px] leading-relaxed text-ink-3">
              <Info className="mt-0.5 size-3.5 shrink-0 text-ink-2" />
              <p>
                Profile = the weaker of the two core ratios, mapped to S&amp;P&apos;s public standard-volatility table. {rp.basis_note}.
                CFO stands in for FFO (not an XBRL concept). Business risk, industry risk and analytical adjustments are out of scope,
                so this is <span className="text-ink-2">not a rating</span>.
              </p>
            </div>
          </div>
        </Panel>
        <Headroom />
      </div>
      <MetricsGrid />
      <div className="grid gap-4 lg:grid-cols-2">
        <ScoreFactors />
        <Altman />
      </div>
    </div>
  );
}

function Headroom() {
  const { doc } = useIssuerCtx();
  const h = doc.risk_profile.headroom;
  const items: { label: string; value: number | null; sub: string; tone: "down" | "up" }[] = [
    { label: "EBITDA decline to next weaker band", value: h.leverage?.ebitda_decline_to_downgrade ?? null,
      sub: h.leverage?.next_threshold ? `until net leverage reaches ${times(h.leverage.next_threshold, 1)}` : "—", tone: "down" },
    { label: "Additional net debt capacity", value: h.leverage?.debt_increase_to_downgrade ?? null,
      sub: h.leverage?.next_threshold ? `before crossing ${times(h.leverage.next_threshold, 1)}` : "—", tone: "down" },
    { label: "CFO decline to next weaker band", value: h.cashflow?.cfo_decline_to_downgrade ?? null,
      sub: h.cashflow?.next_threshold ? `until CFO/net debt falls to ${pct(h.cashflow.next_threshold, 0)}` : "—", tone: "down" },
    { label: "EBITDA growth to next stronger band", value: h.leverage?.ebitda_increase_to_upgrade ?? null,
      sub: h.leverage?.upgrade_threshold ? `to bring net leverage under ${times(h.leverage.upgrade_threshold, 1)}` : "—", tone: "up" },
  ];
  return (
    <Panel eyebrow="Threshold headroom" title="How much room before the band changes?">
      <div className="space-y-5">
        {items.map((it) => (
          <div key={it.label}>
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-[12.5px] text-ink-2">{it.label}</span>
              <span className={cn("num text-[18px] font-semibold", it.value === null ? "text-ink-3" : it.tone === "up" ? "text-ink-1" : it.value < 0.15 ? "text-serious" : "text-ink-1")}>
                {it.value === null ? "—" : pct(it.value, 0)}
              </span>
            </div>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-panel-3">
              {it.value !== null && (
                <div className="h-full rounded-full" style={{ width: `${Math.min(100, it.value * 100)}%`, background: it.tone === "up" ? "var(--series-1)" : it.value < 0.15 ? "var(--serious)" : "var(--series-3)" }} />
              )}
            </div>
            <div className="mt-1 text-[11px] text-ink-3">{it.sub}</div>
          </div>
        ))}
        <p className="num rounded-lg border border-hairline bg-panel-2 p-3 text-[11.5px] leading-relaxed text-ink-3">
          decline = 1 − L/T &nbsp;·&nbsp; capacity = T/L − 1 &nbsp;·&nbsp; L = current ratio, T = next band threshold
        </p>
      </div>
    </Panel>
  );
}

function MetricsGrid() {
  const { doc } = useIssuerCtx();
  const periods = doc.periods;
  const cur = doc.issuer.currency;
  return (
    <Panel eyebrow={`All figures ${cur} · click ✓ to trace`} title="Credit metrics" bodyClassName="p-0">
      <div className="scrollbar-thin overflow-x-auto">
        <table className="w-full min-w-[760px] text-[12.5px]">
          <thead>
            <tr className="border-b border-hairline text-left">
              <th className="label-caps px-5 py-2.5 font-normal">Metric</th>
              {periods.map((p) => (
                <th key={p.id} className={cn("label-caps px-4 py-2.5 text-right font-normal", p.id === doc.primary && "text-amber")}>{p.id}</th>
              ))}
              <th className="label-caps px-5 py-2.5 text-right font-normal">Sector median</th>
            </tr>
          </thead>
          <tbody>
            {GRID.map((row) => {
              const unit = row.kind === "metric" ? metric(doc, doc.primary, row.key)?.unit ?? cur : cur;
              const med = row.peer ? doc.peers?.median?.[row.peer] : undefined;
              return (
                <tr key={row.key} className="border-b border-hairline/60 transition-colors hover:bg-panel-2">
                  <td className="px-5 py-2 text-ink-2">{METRIC_LABELS[row.key]}</td>
                  {periods.map((p) => {
                    const v = row.kind === "metric" ? metric(doc, p.id, row.key)?.value ?? null : fact(doc, p.id, row.key)?.value ?? null;
                    return (
                      <td key={p.id} className="px-4 py-2 text-right">
                        <Tick target={{ kind: row.kind, key: row.key, period: p.id }} className="ml-auto justify-end">
                          <span className={cn("num", v === null ? "text-ink-3" : "text-ink-1")}>
                            {unit === cur ? money(v, "", 2) : fmtMetric(v, unit)}
                          </span>
                        </Tick>
                      </td>
                    );
                  })}
                  <td className="num px-5 py-2 text-right text-ink-3">{med === undefined ? "—" : fmtMetric(med, unit)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function ScoreFactors() {
  const { doc } = useIssuerCtx();
  const s = doc.score[doc.primary];
  return (
    <Panel eyebrow={`Transparent screening heuristic · ${s.method}`} title={
      <span className="flex items-baseline gap-3">Screening score
        <span className="num text-[20px] font-semibold text-ink-1">{s.value === null ? "—" : s.value.toFixed(1)}</span>
        <span className="text-[12px] text-ink-3">{s.value === null ? `range ${s.lower}–${s.upper} (${s.coverage}% of factors available)` : `/ 100 · ${s.band}`}</span>
      </span>}>
      <div className="space-y-3">
        {s.factors.map((f) => (
          <div key={f.name}>
            <div className="flex justify-between text-[12px]">
              <span className="capitalize text-ink-2">{f.name.replace("_", " ")} <span className="text-ink-3">· weight {f.weight}</span></span>
              <span className="num text-ink-1">{f.points === null ? "N/A" : `${f.points.toFixed(0)} pts`}</span>
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-panel-3">
              <div className="h-full rounded-full bg-series-1" style={{ width: `${f.points ?? 0}%`, opacity: f.points === null ? 0 : 0.85 }} />
            </div>
            <p className="mt-1 text-[11px] text-ink-3">{f.explanation}</p>
          </div>
        ))}
        <p className="text-[11px] text-ink-3">Missing factors are never re-weighted: with incomplete evidence the score is shown as a possible range.</p>
      </div>
    </Panel>
  );
}

function Altman() {
  const { doc } = useIssuerCtx();
  const a = doc.altman;
  const pos = a.value === null ? null : Math.min(1, Math.max(0, (a.value + 2) / 12));
  const names: Record<string, string> = {
    working_capital_to_assets: "Working capital / assets × 6.56",
    retained_earnings_to_assets: "Retained earnings / assets × 3.26",
    ebit_to_assets: "EBIT / assets × 6.72",
    equity_to_liabilities: "Book equity / liabilities × 1.05",
  };
  return (
    <Panel eyebrow="Academic distress screen" title={<span className="flex items-baseline gap-3">Altman Z″ <span className="num text-[20px] font-semibold text-ink-1">{a.value === null ? "—" : a.value.toFixed(2)}</span>{a.zone && <span className={cn("text-[12px]", a.zone === "Safe" ? "text-good" : a.zone === "Grey" ? "text-warning" : "text-critical")}>{a.zone} zone</span>}</span>}>
      <div className="relative mt-2">
        <div className="flex h-2.5 overflow-hidden rounded-full">
          <div className="bg-critical/60" style={{ width: `${(3.1 / 12) * 100}%` }} />
          <div className="bg-warning/50" style={{ width: `${(1.5 / 12) * 100}%` }} />
          <div className="flex-1 bg-good/45" />
        </div>
        {pos !== null && <div className="absolute -top-1.5 h-[22px] w-1 -translate-x-1/2 rounded-full bg-ink-1 shadow-[0_0_0_2px_var(--panel)]" style={{ left: `${pos * 100}%` }} />}
        <div className="num mt-1.5 flex justify-between text-[10px] text-ink-3"><span>−2</span><span className="ml-[10%]">1.1</span><span className="mr-[50%]">2.6</span><span>10+</span></div>
      </div>
      {a.components && (
        <div className="mt-4 space-y-1.5">
          {Object.entries(a.components).map(([k, v]) => (
            <div key={k} className="flex justify-between text-[12px]"><span className="text-ink-3">{names[k]}</span><span className="num text-ink-1">{v.toFixed(3)}</span></div>
          ))}
        </div>
      )}
      <p className="mt-4 text-[11px] leading-relaxed text-ink-3">
        Z″ = 6.56·X1 + 3.26·X2 + 6.72·X3 + 1.05·X4 (Altman, 1995 non-manufacturing version). Zones: &gt;2.6 safe, 1.1–2.6 grey, &lt;1.1 distress. A screening model, not a default probability.
      </p>
    </Panel>
  );
}

export { TIERS };
