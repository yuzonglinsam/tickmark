"use client";

import { useMemo, useState } from "react";
import { ArrowRight, RotateCcw, TrendingDown } from "lucide-react";
import { Slider } from "@/components/ui/slider";
import { Panel } from "@/components/common/panel";
import { TierChip } from "@/components/common/tier-chip";
import { EChart, C, axisCommon, baseTooltip } from "@/components/charts/echart";
import { runScenario, scenarioBase, type ScenarioInput } from "@/lib/issuer";
import { LEVERAGE_BOUNDS, money, pct, times, TIERS } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useIssuerCtx } from "./source-context";
import { TierLadder } from "./tier-ladder";

const ZERO: ScenarioInput = { ebitda: 0, interest: 0, cfo: 0, debt: 0 };
const PRESETS: { name: string; desc: string; s: ScenarioInput }[] = [
  { name: "Mild downturn", desc: "EBITDA −10%, CFO −15%", s: { ebitda: -0.1, interest: 0, cfo: -0.15, debt: 0 } },
  { name: "Recession", desc: "EBITDA −25%, CFO −30%", s: { ebitda: -0.25, interest: 0.1, cfo: -0.3, debt: 0 } },
  { name: "Rate shock", desc: "Interest cost +100%", s: { ebitda: 0, interest: 1, cfo: -0.05, debt: 0 } },
  { name: "Debt-funded M&A", desc: "Debt +35%, EBITDA +8%", s: { ebitda: 0.08, interest: 0.3, cfo: 0.05, debt: 0.35 } },
  { name: "Severe stress", desc: "EBITDA −40%, CFO −45%, rates +50%", s: { ebitda: -0.4, interest: 0.5, cfo: -0.45, debt: 0.05 } },
];

export function ScenarioLab() {
  const { doc } = useIssuerCtx();
  const cur = doc.issuer.currency;
  const base = useMemo(() => scenarioBase(doc), [doc]);
  const [s, setS] = useState<ScenarioInput>(ZERO);
  const b = useMemo(() => runScenario(base, ZERO), [base]);
  const r = useMemo(() => runScenario(base, s), [base, s]);
  const moved = r.overall !== null && b.overall !== null ? r.overall - b.overall : null;
  const unavailable = base.debt === null || base.ebitda === null;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-[380px_1fr]">
        <Panel eyebrow="Shocks · % of |base|" title="Scenario inputs"
          action={<button onClick={() => setS(ZERO)} className="inline-flex items-center gap-1 text-[12px] text-ink-3 hover:text-ink-1"><RotateCcw className="size-3.5" /> Reset</button>}>
          <div className="space-y-6">
            <Shock label="EBITDA" value={s.ebitda} min={-0.7} max={0.3} onChange={(v) => setS({ ...s, ebitda: v })} base={money(base.ebitda, cur)} />
            <Shock label="Operating cash flow" value={s.cfo} min={-0.7} max={0.3} onChange={(v) => setS({ ...s, cfo: v })} base={money(base.cfo, cur)} />
            <Shock label="Interest cost" value={s.interest} min={0} max={2} onChange={(v) => setS({ ...s, interest: v })} base={money(base.interest, cur)} invert />
            <Shock label="Gross debt" value={s.debt} min={-0.3} max={0.6} onChange={(v) => setS({ ...s, debt: v })} base={money(base.debt, cur)} invert />
            <div>
              <div className="label-caps mb-2">Presets</div>
              <div className="grid grid-cols-1 gap-1.5">
                {PRESETS.map((p) => (
                  <button key={p.name} onClick={() => setS(p.s)}
                    className="flex items-center justify-between rounded-lg border border-hairline bg-panel-2 px-3 py-2 text-left transition-colors hover:border-amber/40">
                    <span className="text-[12.5px] text-ink-1">{p.name}</span>
                    <span className="text-[11px] text-ink-3">{p.desc}</span>
                  </button>
                ))}
              </div>
            </div>
            <p className="text-[11px] leading-relaxed text-ink-3">
              Static sensitivity, recomputed in your browser with the same rules as the Python engine: shocks scale |base| so a
              loss deepens rather than flips; cash and short-term investments are held constant. Not a forecast. No AI involved.
            </p>
          </div>
        </Panel>
        <div className="space-y-4">
          <Panel eyebrow="Result" title="Indicative financial risk under the scenario">
            {unavailable ? (
              <p className="text-[13px] text-ink-3">Debt or EBITDA is unavailable for this issuer, so the leverage scenario cannot be computed. Missing inputs are never assumed to be zero.</p>
            ) : (
              <div className="space-y-6">
                <div className="flex flex-wrap items-center gap-3">
                  <TierChip tier={b.overall} className="text-[12px]" />
                  <ArrowRight className="size-4 text-ink-3" />
                  <TierChip tier={r.overall} className="text-[12px]" />
                  {moved !== null && moved !== 0 && (
                    <span className={cn("ml-1 rounded-md px-2 py-0.5 text-[11.5px] font-medium", moved > 0 ? "bg-critical/15 text-critical" : "bg-good/15 text-good")}>
                      {moved > 0 ? `▼ ${moved} band${moved > 1 ? "s" : ""} weaker` : `▲ ${-moved} band${moved < -1 ? "s" : ""} stronger`}
                    </span>
                  )}
                  {moved === 0 && <span className="text-[12px] text-ink-3">Band unchanged</span>}
                  {r.burning && <span className="rounded-md bg-warning/15 px-2 py-0.5 text-[11.5px] text-warning">Negative EBITDA/CFO — ratios not meaningful</span>}
                </div>
                <div className="grid gap-6 md:grid-cols-2">
                  <TierLadder label="Net debt / EBITDA" kind="leverage" value={r.leverage} tier={r.levTier} ghost={{ value: b.leverage, tier: b.levTier }} />
                  <TierLadder label="CFO / net debt" kind="cashflow" value={r.cashflow} tier={r.cfTier} ghost={{ value: b.cashflow, tier: b.cfTier }} />
                </div>
                <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                  <Delta label="Net leverage" a={times(b.leverage)} b={times(r.leverage)} worse={(r.leverage ?? 0) > (b.leverage ?? 0)} />
                  <Delta label="CFO / net debt" a={pct(b.cashflow, 0)} b={pct(r.cashflow, 0)} worse={(r.cashflow ?? 0) < (b.cashflow ?? 0)} />
                  <Delta label="EBITDA / interest" a={times(b.coverage, 1)} b={times(r.coverage, 1)} worse={(r.coverage ?? 0) < (b.coverage ?? 0)} />
                  <Delta label="Net debt" a={money(b.netDebt)} b={money(r.netDebt)} worse={(r.netDebt ?? 0) > (b.netDebt ?? 0)} />
                </div>
              </div>
            )}
          </Panel>
          {!unavailable && <BreakpointChart base={base} s={s} />}
        </div>
      </div>
      {!unavailable && <Tornado base={base} />}
    </div>
  );
}

function Shock({ label, value, min, max, onChange, base, invert }: {
  label: string; value: number; min: number; max: number; onChange: (v: number) => void; base: string; invert?: boolean;
}) {
  const bad = invert ? value > 0 : value < 0;
  return (
    <div>
      <div className="mb-2.5 flex items-baseline justify-between">
        <span className="text-[13px] text-ink-1">{label}</span>
        <span className={cn("num text-[14px] font-semibold", value === 0 ? "text-ink-3" : bad ? "text-serious" : "text-good")}>
          {value > 0 ? "+" : ""}{(value * 100).toFixed(0)}%
        </span>
      </div>
      <div className="relative">
        <Slider value={[value]} min={min} max={max} step={0.01} onValueChange={([v]) => onChange(Math.round(v * 100) / 100)}
          className="[&_[data-slot=slider-range]]:bg-transparent" />
        <div className="pointer-events-none absolute top-1/2 h-1.5 -translate-y-1/2 rounded-full"
          style={{
            left: `${((Math.min(0, value) - min) / (max - min)) * 100}%`,
            width: `${(Math.abs(value) / (max - min)) * 100}%`,
            background: value === 0 ? "transparent" : bad ? "var(--serious)" : "var(--good)",
          }} />
        <div className="pointer-events-none absolute top-1/2 h-3 w-px -translate-y-1/2 bg-ink-3" style={{ left: `${((0 - min) / (max - min)) * 100}%` }} />
      </div>
      <div className="num mt-1.5 text-[10.5px] text-ink-3">base {base}</div>
    </div>
  );
}

function Delta({ label, a, b, worse }: { label: string; a: string; b: string; worse: boolean }) {
  const same = a === b;
  return (
    <div className="rounded-lg border border-hairline bg-panel-2 p-3">
      <div className="text-[11px] text-ink-3">{label}</div>
      <div className="num mt-1 text-[11.5px] text-ink-3 line-through decoration-ink-3/50">{same ? "" : a}</div>
      <div className={cn("num text-[17px] font-semibold", same ? "text-ink-1" : worse ? "text-serious" : "text-good")}>{b}</div>
    </div>
  );
}

function BreakpointChart({ base, s }: { base: ReturnType<typeof scenarioBase>; s: ScenarioInput }) {
  const xs = Array.from({ length: 71 }, (_, i) => -i / 100);
  const pts = xs.map((x) => {
    const r = runScenario(base, { ...s, ebitda: x });
    return [x * 100, r.leverage === null ? null : Math.min(r.leverage, 9)];
  });
  const cur = runScenario(base, s);
  const baseLev = runScenario(base, { ...s, ebitda: 0 }).leverage ?? 0;
  const crossings = LEVERAGE_BOUNDS.filter((t) => t > baseLev).map((t) => {
    const hit = pts.find((p) => p[1] !== null && (p[1] as number) >= t);
    return hit ? { t, x: hit[0] as number } : null;
  }).filter(Boolean) as { t: number; x: number }[];
  const bands = [0, ...LEVERAGE_BOUNDS, 9];
  return (
    <Panel eyebrow="Breakpoints" title={<span className="inline-flex items-center gap-2"><TrendingDown className="size-4 text-ink-3" /> Net leverage as EBITDA falls (other shocks held at current settings)</span>}>
      <EChart
        height={250}
        option={{
          grid: { left: 8, right: 16, top: 12, bottom: 4, containLabel: true },
          tooltip: { ...baseTooltip, formatter: (p: unknown) => {
            const a = (p as { value: [number, number] }[])[0];
            return `EBITDA ${a.value[0].toFixed(0)}%<br/><b>${a.value[1] === null ? "n.m." : a.value[1].toFixed(2) + "x"}</b> net leverage`;
          } },
          xAxis: { type: "value", min: -70, max: 0, inverse: true, ...axisCommon, splitLine: { show: false },
            axisLabel: { ...axisCommon.axisLabel, formatter: (v: number) => `${v}%` }, name: "EBITDA change", nameLocation: "middle", nameGap: 26, nameTextStyle: { color: C.ink3, fontSize: 11 } },
          yAxis: { type: "value", min: 0, max: 9, ...axisCommon, axisLine: { show: false }, axisLabel: { ...axisCommon.axisLabel, formatter: (v: number) => `${v}x` } },
          series: [{
            type: "line", data: pts, showSymbol: false, smooth: false, lineStyle: { width: 2, color: C.ink1 }, connectNulls: false,
            markArea: { silent: true, data: bands.slice(0, -1).map((lo, i) => [{ yAxis: lo, itemStyle: { color: C.tiers[i], opacity: 0.09 } }, { yAxis: bands[i + 1] }]) },
            markLine: { silent: true, symbol: "none", label: { show: false },
              lineStyle: { color: "#283340", type: "dashed" }, data: LEVERAGE_BOUNDS.map((b) => ({ yAxis: b })) },
          },
          {
            type: "scatter", symbolSize: 12, z: 5,
            data: cur.leverage !== null ? [[s.ebitda * 100, Math.min(cur.leverage, 9)]] : [],
            itemStyle: { color: C.amber, borderColor: C.panel, borderWidth: 2 },
            label: { show: true, position: "top", color: C.amber, fontSize: 11, fontFamily: "JetBrains Mono Variable",
              formatter: () => `scenario ${times(cur.leverage)}` },
          }],
        }}
      />
      {crossings.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {crossings.map((c) => (
            <span key={c.t} className="num rounded-md border border-hairline bg-panel-2 px-2 py-1 text-[11px] text-ink-2">
              {times(c.t, 1)} at EBITDA {c.x.toFixed(0)}% → {TIERS[LEVERAGE_BOUNDS.indexOf(c.t) + 1]}
            </span>
          ))}
        </div>
      )}
    </Panel>
  );
}

function Tornado({ base: baseInputs }: { base: ReturnType<typeof scenarioBase> }) {
  const b0 = runScenario(baseInputs, ZERO);
  const charts: { title: string; fmt: (v: number) => string; pick: (r: ReturnType<typeof runScenario>) => number | null; rows: [string, ScenarioInput, ScenarioInput][] }[] = [
    { title: `Net debt / EBITDA · base ${times(b0.leverage)}`, fmt: (v) => `${v > 0 ? "+" : ""}${v.toFixed(2)}x`, pick: (r) => r.leverage,
      rows: [["EBITDA ±20%", { ...ZERO, ebitda: -0.2 }, { ...ZERO, ebitda: 0.2 }], ["Debt ±20%", { ...ZERO, debt: 0.2 }, { ...ZERO, debt: -0.2 }]] },
    { title: `EBITDA / interest · base ${times(b0.coverage, 1)}`, fmt: (v) => `${v > 0 ? "+" : ""}${v.toFixed(1)}x`, pick: (r) => r.coverage,
      rows: [["EBITDA ±20%", { ...ZERO, ebitda: -0.2 }, { ...ZERO, ebitda: 0.2 }], ["Interest ±20%", { ...ZERO, interest: 0.2 }, { ...ZERO, interest: -0.2 }]] },
    { title: `CFO / net debt · base ${pct(b0.cashflow, 0)}`, fmt: (v) => `${v > 0 ? "+" : ""}${(v * 100).toFixed(0)}pp`, pick: (r) => r.cashflow,
      rows: [["CFO ±20%", { ...ZERO, cfo: -0.2 }, { ...ZERO, cfo: 0.2 }], ["Debt ±20%", { ...ZERO, debt: 0.2 }, { ...ZERO, debt: -0.2 }]] },
  ];
  return (
    <Panel eyebrow="One shock at a time, ±20%" title="Sensitivity — what moves each ratio?">
      <div className="grid gap-4 md:grid-cols-3">
        {charts.map((c) => {
          const base = c.pick(b0);
          const data = c.rows.map(([l, bad, good]) => {
            const vb = c.pick(runScenario(baseInputs, bad));
            const vg = c.pick(runScenario(baseInputs, good));
            return { l, bad: vb === null || base === null ? 0 : vb - base, good: vg === null || base === null ? 0 : vg - base };
          });
          return (
            <div key={c.title} className="rounded-lg border border-hairline bg-panel-2 p-3">
              <div className="text-[12px] text-ink-2">{c.title}</div>
              <EChart height={120} option={{
                grid: { left: 4, right: 18, top: 8, bottom: 0, containLabel: true },
                tooltip: { ...baseTooltip, trigger: "item", formatter: (p: unknown) => { const q = p as { name: string; value: number; seriesName: string }; return `${q.name} · ${q.seriesName}<br/><b>${c.fmt(q.value)}</b>`; } },
                xAxis: { type: "value", ...axisCommon, axisLabel: { ...axisCommon.axisLabel, formatter: (v: number) => c.fmt(v) } },
                yAxis: { type: "category", data: data.map((r) => r.l), inverse: true, ...axisCommon, splitLine: { show: false }, axisLabel: { ...axisCommon.axisLabel, fontFamily: "Inter Variable", color: C.ink2 } },
                series: [
                  { name: "Adverse", type: "bar", data: data.map((r) => r.bad), barWidth: 14, itemStyle: { color: C.s2, borderRadius: 3 } },
                  { name: "Favourable", type: "bar", barGap: "-100%", data: data.map((r) => r.good), barWidth: 14, itemStyle: { color: C.s1, borderRadius: 3 } },
                ],
              }} />
            </div>
          );
        })}
      </div>
    </Panel>
  );
}
