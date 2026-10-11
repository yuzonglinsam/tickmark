"use client";

import { Panel } from "@/components/common/panel";
import { EChart, C, axisCommon, baseTooltip } from "@/components/charts/echart";
import { annualPeriods, fact, mval } from "@/lib/issuer";
import { METRIC_LABELS, money, pct, axisMoney } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useIssuerCtx } from "./source-context";
import { Tick } from "./tick";

export function CashFlow() {
  const { doc } = useIssuerCtx();
  const cur = doc.issuer.currency;
  const pid = doc.primary;
  const v = (k: string) => fact(doc, pid, k)?.value ?? null;
  const cfo = v("operating_cash_flow");
  const steps: [string, number | null, "total" | "out"][] = [
    ["Operating cash flow", cfo, "total"],
    ["Capex", v("capex"), "out"],
    ["Free cash flow", mval(doc, pid, "fcf"), "total"],
    ["Dividends", v("dividends"), "out"],
    ["Buybacks", v("buybacks"), "out"],
    ["Acquisitions", v("acquisitions"), "out"],
  ];
  const fcf = mval(doc, pid, "fcf");
  const residual = fcf === null ? null : fcf - (v("dividends") ?? 0) - (v("buybacks") ?? 0) - (v("acquisitions") ?? 0);
  steps.push(["After distributions & M&A", residual, "total"]);
  // Each step is a floating range [lo, hi]; split into positive/negative parts so
  // ECharts' same-sign stacking draws ranges that cross zero correctly.
  const ranges: ([number, number] | null)[] = [];
  let level = 0;
  for (const [, val, kind] of steps) {
    if (val === null) { ranges.push(null); continue; }
    if (kind === "total") { level = val; ranges.push([Math.min(0, val), Math.max(0, val)]); }
    else { const next = level - val; ranges.push([Math.min(level, next), Math.max(level, next)]); level = next; }
  }
  const pick = (f: (lo: number, hi: number) => number) => ranges.map((r) => (r ? f(r[0], r[1]) : "-"));
  const posBase = pick((lo) => Math.max(0, lo));
  const posFill = pick((lo, hi) => Math.max(0, hi) - Math.max(0, lo));
  const negBase = pick((_, hi) => Math.min(0, hi));
  const negFill = pick((lo, hi) => Math.min(0, lo) - Math.min(0, hi));
  const color = steps.map(([, , kind], i) => (kind === "total" ? ((ranges[i]?.[0] ?? 0) < 0 ? C.critical : C.s1) : C.s2));
  const srf = mval(doc, pid, "shareholder_returns_to_fcf");
  const rows = ["operating_cash_flow", "capex", "fcf", "dividends", "buybacks", "acquisitions", "debt_issued", "debt_repaid", "interest_paid", "sbc"];
  const periods = annualPeriods(doc);
  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <Panel eyebrow={`${pid} · ${cur}`} title="Where did the cash go?">
          <EChart
            height={300}
            option={{
              grid: { left: 8, right: 8, top: 16, bottom: 4, containLabel: true },
              tooltip: { ...baseTooltip, trigger: "axis", formatter: (p: unknown) => {
                const arr = p as { dataIndex: number }[];
                const s = steps[arr[0].dataIndex];
                return `${s[0]}<br/><b>${s[1] === null ? "N/A (not tagged)" : (s[2] === "out" ? "−" : "") + money(s[1], cur)}</b>`;
              } },
              xAxis: { type: "category", data: steps.map((s) => s[0]), ...axisCommon, splitLine: { show: false }, axisLabel: { ...axisCommon.axisLabel, interval: 0, fontFamily: "Inter Variable", fontSize: 10.5, width: 80, overflow: "break" } },
              yAxis: { type: "value", ...axisCommon, axisLine: { show: false }, axisLabel: { ...axisCommon.axisLabel, formatter: axisMoney } },
              series: [
                { type: "bar", stack: "w", data: posBase, itemStyle: { color: "transparent" }, emphasis: { disabled: true }, barMaxWidth: 46 },
                { type: "bar", stack: "w", data: posFill.map((v, i) => ({ value: v, itemStyle: { color: color[i], borderRadius: 3 } })), barMaxWidth: 46 },
                { type: "bar", stack: "w", data: negBase, itemStyle: { color: "transparent" }, emphasis: { disabled: true }, barMaxWidth: 46 },
                { type: "bar", stack: "w", data: negFill.map((v, i) => ({ value: v, itemStyle: { color: color[i], borderRadius: 3 } })), barMaxWidth: 46 },
              ],
            }}
          />
          <p className="mt-2 text-[11px] text-ink-3">Blue = cash available, orange = cash used, red = shortfall funded from the balance sheet or borrowing. Untagged items (N/A) are skipped, not treated as zero.</p>
        </Panel>
        <Panel eyebrow="Creditor lens" title="Are shareholders paid from free cash flow?">
          <div className="space-y-4">
            <div>
              <div className="label-caps">Dividends + buybacks / FCF</div>
              <div className={cn("num mt-1.5 text-[34px] font-semibold tracking-tight", srf === null ? "text-ink-3" : srf > 1 ? "text-serious" : "text-ink-1")}>
                <Tick target={{ kind: "metric", key: "shareholder_returns_to_fcf", period: pid }}>{srf === null ? "N/A" : pct(srf, 0)}</Tick>
              </div>
            </div>
            <p className="text-[13px] leading-relaxed text-ink-2">
              {srf === null ? "Not computable: free cash flow is negative or distributions are not tagged." :
                srf > 1 ? "Distributions exceed free cash flow — the gap is funded from the balance sheet or new borrowing, a classic creditor-unfriendly signal worth monitoring." :
                srf > 0.75 ? "Most free cash flow is returned to shareholders, leaving limited internal capacity for debt reduction." :
                "Distributions are comfortably covered by free cash flow, leaving room to reduce debt or absorb a downturn."}
            </p>
            <div className="grid grid-cols-2 gap-2 text-[12px]">
              <MiniStat label="Debt issued" v={money(v("debt_issued"), "", 2)} />
              <MiniStat label="Debt repaid" v={money(v("debt_repaid"), "", 2)} />
              <MiniStat label="Cash interest paid" v={money(v("interest_paid"), "", 2)} />
              <MiniStat label="Stock-based comp" v={money(v("sbc"), "", 2)} />
            </div>
          </div>
        </Panel>
      </div>
      <Panel eyebrow={`Cash-flow statement items · ${cur}`} title="Three-year history" bodyClassName="p-0">
        <div className="scrollbar-thin overflow-x-auto">
          <table className="w-full min-w-[560px] text-[12.5px]">
            <thead>
              <tr className="border-b border-hairline text-left">
                <th className="label-caps px-5 py-2.5 font-normal">Item</th>
                {periods.map((p) => <th key={p.id} className="label-caps px-5 py-2.5 text-right font-normal">{p.id}</th>)}
              </tr>
            </thead>
            <tbody>
              {rows.map((k) => (
                <tr key={k} className="border-b border-hairline/60 hover:bg-panel-2">
                  <td className="px-5 py-2 text-ink-2">{METRIC_LABELS[k]}</td>
                  {periods.map((p) => {
                    const val = k === "fcf" ? mval(doc, p.id, k) : fact(doc, p.id, k)?.value ?? null;
                    return (
                      <td key={p.id} className="px-5 py-2 text-right">
                        <Tick target={{ kind: k === "fcf" ? "metric" : "fact", key: k, period: p.id }} className="ml-auto">
                          <span className={cn("num", val === null ? "text-ink-3" : "text-ink-1")}>{money(val, "", 2)}</span>
                        </Tick>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function MiniStat({ label, v }: { label: string; v: string }) {
  return (
    <div className="rounded-lg border border-hairline bg-panel-2 px-3 py-2">
      <div className="text-[10.5px] text-ink-3">{label}</div>
      <div className="num mt-0.5 text-ink-1">{v}</div>
    </div>
  );
}
