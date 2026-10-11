"use client";

import { ArrowUpRight, CircleAlert } from "lucide-react";
import { Panel, Stat } from "@/components/common/panel";
import { EChart, C, axisCommon, baseTooltip } from "@/components/charts/echart";
import { fact, mval } from "@/lib/issuer";
import { fmtDate, money, pct, times, axisMoney } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useIssuerCtx } from "./source-context";
import { Tick } from "./tick";
import { Legend } from "./overview";

export function DebtLiquidity() {
  const { doc, trace } = useIssuerCtx();
  const cur = doc.issuer.currency;
  const pid = doc.primary;
  const end = doc.periods.find((p) => p.id === pid)!.end;
  const fy = Number(end.slice(0, 4));
  const ladder = doc.maturities;
  const liquid = doc.risk_profile.liquid_assets;
  const debt = fact(doc, pid, "debt")?.value ?? null;
  const fcf = mval(doc, pid, "fcf");
  const labels = ladder.map((m, i) => (i < 5 ? `${fy + i + 1}` : `${fy + 6}+`));
  const vals = ladder.map((m) => m.value);
  const next12 = vals[0] ?? null;
  const within3 = vals.slice(0, 3).reduce<number>((a, v) => a + (v ?? 0), 0);
  const totalLadder = vals.reduce<number>((a, v) => a + (v ?? 0), 0);
  const cumMat = vals.reduce<number[]>((acc, v) => [...acc, (acc[acc.length - 1] ?? 0) + (v ?? 0)], []);
  const runway = vals.map((_, i) => (liquid === null ? null : liquid + Math.max(0, fcf ?? 0) * (i + 1)));
  const coveredThrough = runway.findIndex((r, i) => r !== null && r < cumMat[i]);
  const scope = doc.debt_scope;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div className="panel p-4">
          <Stat label="Debt" value={<Tick target={{ kind: "fact", key: "debt", period: pid }}>{money(debt, "", 2)}</Tick>} sub={`${cur} · scope ${scope.completeness}`} />
        </div>
        <div className="panel p-4"><Stat label="Cash + ST investments" value={money(liquid, "", 2)} sub={cur} /></div>
        <div className="panel p-4">
          <Stat label="Liquidity / next-12m maturities" value={next12 ? times(liquid !== null ? liquid / next12 : null, 1) : "—"} sub={next12 ? `${money(next12, cur)} due within a year` : "No maturity schedule tagged"} />
        </div>
        <div className="panel p-4">
          <Stat label="Due within 3 years" value={totalLadder ? pct(within3 / totalLadder, 0) : "—"} sub="of scheduled principal" />
        </div>
      </div>

      {ladder.length > 0 ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Panel eyebrow={`Contractual principal maturities · ${cur} · from the ${doc.filings.annual?.form ?? "annual"} debt note`} title="Maturity wall"
            action={<Legend items={[["Principal due", C.s1], ["Cash + ST investments", C.amber]]} />}>
            <EChart
              height={280}
              option={{
                grid: { left: 8, right: 12, top: 18, bottom: 4, containLabel: true },
                tooltip: { ...baseTooltip, valueFormatter: (v) => money(v as number, cur) },
                xAxis: { type: "category", data: labels, ...axisCommon, splitLine: { show: false } },
                yAxis: { type: "value", ...axisCommon, axisLine: { show: false }, axisLabel: { ...axisCommon.axisLabel, formatter: axisMoney } },
                series: [{
                  name: "Principal due", type: "bar", data: vals, barMaxWidth: 42,
                  itemStyle: { color: C.s1, borderRadius: [4, 4, 0, 0] },
                  markLine: liquid ? { symbol: "none", label: { color: C.amber, fontSize: 10.5, formatter: "cash + ST inv." }, lineStyle: { color: C.amber, type: "dashed", width: 1.5 }, data: [{ yAxis: liquid }] } : undefined,
                }],
              }}
              onEvents={{ click: (p: unknown) => {
                const idx = (p as { dataIndex: number }).dataIndex;
                const src = ladder[idx]?.source?.ref;
                if (src) trace({ kind: "source", id: src });
              } }}
            />
            <p className="mt-2 text-[11px] text-ink-3">Click a bar to trace its XBRL tag. Buckets are relative to the balance-sheet date ({fmtDate(end)}).</p>
          </Panel>
          <Panel eyebrow="Illustrative · assumes FCF stays at the latest fiscal-year level" title="Liquidity runway"
            action={<Legend items={[["Cumulative maturities", C.muted], ["Liquidity + cumulative FCF", C.s3]]} />}>
            <EChart
              height={280}
              option={{
                grid: { left: 8, right: 12, top: 18, bottom: 4, containLabel: true },
                tooltip: { ...baseTooltip, valueFormatter: (v) => money(v as number, cur) },
                xAxis: { type: "category", data: labels, ...axisCommon, splitLine: { show: false } },
                yAxis: { type: "value", ...axisCommon, axisLine: { show: false }, axisLabel: { ...axisCommon.axisLabel, formatter: axisMoney } },
                series: [
                  { name: "Cumulative maturities", type: "bar", data: cumMat, barMaxWidth: 42, itemStyle: { color: C.muted, borderRadius: [4, 4, 0, 0] } },
                  { name: "Liquidity + cumulative FCF", type: "line", data: runway, symbolSize: 7, lineStyle: { width: 2, color: C.s3 }, itemStyle: { color: C.s3 } },
                ],
              }}
            />
            <p className={cn("mt-2 text-[12px]", coveredThrough === -1 ? "text-good" : "text-warning")}>
              {liquid === null ? "Cash unavailable." :
                coveredThrough === -1 ? "Scheduled maturities are covered by existing liquidity plus retained free cash flow across the whole schedule — no refinancing needed on this simple test." :
                `Liquidity plus FCF falls short of cumulative maturities by ${labels[coveredThrough]} — refinancing or new funding would be needed from then.`}
            </p>
          </Panel>
        </div>
      ) : (
        <Panel title="Maturity wall">
          <p className="flex items-center gap-2 text-[13px] text-ink-3"><CircleAlert className="size-4" /> This issuer did not tag a principal-maturity schedule (LongTermDebtMaturitiesRepaymentsOfPrincipal…) in XBRL, so no ladder is drawn.</p>
        </Panel>
      )}

      <Panel eyebrow={scope.definition} title={<span className="flex items-center gap-2">How debt was built <span className={cn("rounded px-1.5 py-0.5 text-[10.5px] font-medium", scope.completeness === "full" ? "bg-good/15 text-good" : scope.completeness === "partial" ? "bg-warning/15 text-warning" : "bg-panel-3 text-ink-3")}>{scope.completeness}</span></span>}
        action={<button onClick={() => trace({ kind: "debt" })} className="text-[12px] text-amber hover:underline">Open trace</button>}>
        <div className="space-y-2">
          {scope.components.map((c, i) => (
            <a key={i} href={c.url} target="_blank" rel="noreferrer" className="flex items-center justify-between gap-4 rounded-lg border border-hairline bg-panel-2 px-4 py-2.5 transition-colors hover:border-amber/40">
              <div className="min-w-0">
                <div className="text-[13px] text-ink-1">{c.label}</div>
                <div className="num truncate text-[11px] text-ink-3">{c.concept} · {c.form} filed {fmtDate(c.filed)}</div>
              </div>
              <span className="num inline-flex items-center gap-1 text-[14px] text-ink-1">{money(c.value, "", 2)} <ArrowUpRight className="size-3 text-ink-3" /></span>
            </a>
          ))}
          {Object.entries(scope.leases).map(([k, c]) => (
            <div key={k} className="flex items-center justify-between gap-4 rounded-lg border border-dashed border-hairline-strong px-4 py-2.5 text-ink-3">
              <div className="text-[12.5px]">{k.replace(/([A-Z])/g, " $1").trim()} <span className="text-[11px]">· excluded from debt</span></div>
              <span className="num text-[13px]">{money(c.value, "", 2)}</span>
            </div>
          ))}
          {scope.not_tagged.length > 0 && (
            <p className="pt-1 text-[12px] text-ink-3">Not separately tagged (never assumed zero): {scope.not_tagged.join("; ")}.</p>
          )}
        </div>
      </Panel>
    </div>
  );
}
