"use client";

import Link from "next/link";
import { ArrowRight, ArrowDownRight, ArrowUpRight, CircleCheck, FileWarning, Quote, ShieldCheck } from "lucide-react";
import { useUniverse } from "@/lib/data";
import { TierChip } from "@/components/common/tier-chip";
import { FX_SIZING, titleCase } from "@/lib/format";
import { Panel } from "@/components/common/panel";
import { Sparkline } from "@/components/common/sparkline";
import { EChart, C, axisCommon, baseTooltip } from "@/components/charts/echart";
import { fact, metric, prevAnnual, series, annualPeriods } from "@/lib/issuer";
import { fmtMetric, METRIC_LABELS, money, pct, times, TIERS, axisMoney } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useIssuerCtx } from "./source-context";
import { Tick } from "./tick";
import { TierLadder } from "./tier-ladder";

const KPIS: { key: string; kind: "fact" | "metric"; better: "up" | "down"; peer?: string }[] = [
  { key: "revenue", kind: "fact", better: "up", peer: "g" },
  { key: "ebitda_proxy", kind: "metric", better: "up", peer: "om" },
  { key: "fcf", kind: "metric", better: "up", peer: "fcfd" },
  { key: "net_leverage_adj", kind: "metric", better: "down", peer: "nlev" },
  { key: "ebitda_coverage", kind: "metric", better: "up", peer: "ecov" },
  { key: "cfo_to_debt", kind: "metric", better: "up", peer: "cfod" },
];

export function Overview({ onTab }: { onTab: (t: string) => void }) {
  const { doc, period } = useIssuerCtx();
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {KPIS.map((k) => <KpiCard key={k.key} mkey={k.key} kind={k.kind} better={k.better} peer={k.peer} pid={period} />)}
      </div>
      <div className="grid gap-4 lg:grid-cols-[1.55fr_1fr]">
        <HistoryChart />
        <RiskCard onTab={onTab} />
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <PeerPosition />
        <MemoTeaser onTab={onTab} />
        <Integrity onTab={onTab} />
      </div>
      <SectorPeers />
      <p className="text-center text-[11.5px] text-ink-3">
        Dataset built {doc.generated_at.slice(0, 10)} · evidence cut-off {doc.as_of}. Financial coverage: {doc.periods.find((p) => p.id === period)?.start} to {doc.periods.find((p) => p.id === period)?.end} ({period}). Standalone quarters: {doc.periods.filter((p) => p.basis === "quarter").map((p) => p.id).join(", ") || "none available"}. Missing quarters are unavailable, not zero; a recent refresh does not imply recent financial coverage. Click any <span className="text-amber">✓</span> to trace it.
      </p>
    </div>
  );
}

function KpiCard({ mkey: k, kind, better, pid, peer }: { mkey: string; kind: "fact" | "metric"; better: "up" | "down"; pid: string; peer?: string }) {
  const { doc } = useIssuerCtx();
  const cur = doc.issuer.currency;
  const m = kind === "metric" ? metric(doc, pid, k) : null;
  const f = kind === "fact" ? fact(doc, pid, k) : null;
  const value = m ? m.value : f?.value ?? null;
  const unit = m ? m.unit : cur;
  const prev = prevAnnual(doc, pid);
  const pv = prev ? (kind === "metric" ? metric(doc, prev, k)?.value : fact(doc, prev, k)?.value) ?? null : null;
  let delta: number | null = null;
  let deltaText = "";
  const netCashEither = k === "net_leverage_adj" && ((value ?? 1) <= 0 || (pv ?? 1) <= 0);
  if (value !== null && pv !== null && !netCashEither) {
    if (unit === cur && pv !== 0) {
      delta = (value - pv) / Math.abs(pv);
      deltaText = pct(delta, 1, true);
    } else if (unit === "ratio") {
      delta = value - pv;
      deltaText = `${delta > 0 ? "+" : ""}${(delta * 100).toFixed(1)}pp`;
    } else if (unit === "x") {
      delta = value - pv;
      deltaText = `${delta > 0 ? "+" : ""}${delta.toFixed(2)}x`;
    }
  }
  const good = delta === null ? null : better === "up" ? delta > 0 : delta < 0;
  const s = series(doc, k).map((x) => x.value);
  const pctl = peer ? doc.peers?.percentile?.[peer] : undefined;
  return (
    <div className="panel group relative flex flex-col justify-between gap-3 p-4 transition-colors hover:border-hairline-strong">
      <div className="flex items-start justify-between gap-2">
        <div className="text-[12px] text-ink-3">{METRIC_LABELS[k]}{unit === cur && <span className="num ml-1.5 text-[10px] text-ink-3/80">{cur}</span>}</div>
        <Sparkline values={s} width={64} height={22} color={good === false ? C.s2 : C.s1} />
      </div>
      <Tick target={{ kind, key: k, period: pid }} className="w-fit">
        <span className="num text-[22px] font-semibold leading-none tracking-tight text-ink-1">
          {k === "net_leverage_adj" && value !== null && value <= 0 ? "Net cash" : unit === cur ? money(value, "", 2) : fmtMetric(value, unit, cur)}
        </span>
      </Tick>
      <div className="flex items-center justify-between gap-2 text-[11.5px]">
        {delta !== null ? (
          <span className={cn("num inline-flex items-center gap-0.5", good ? "text-good" : "text-serious")}>
            {delta > 0 ? <ArrowUpRight className="size-3" /> : <ArrowDownRight className="size-3" />}
            {deltaText}
            <span className="ml-1 text-ink-3">vs {prev}</span>
          </span>
        ) : (
          <span className="text-ink-3">{value === null ? "N/A — see trace" : unit === cur ? cur : "—"}</span>
        )}
      </div>
      {pctl !== undefined && (
        <div className="space-y-1">
          <div className="relative h-1 overflow-hidden rounded-full bg-panel-3">
            <div className="absolute inset-y-0 left-0 rounded-full bg-series-1/70" style={{ width: `${Math.round(pctl * 100)}%` }} />
          </div>
          <div className="text-[10.5px] text-ink-3">Stronger than {Math.round(pctl * 100)}% of sector peers</div>
        </div>
      )}
    </div>
  );
}

function HistoryChart() {
  const { doc } = useIssuerCtx();
  const cur = doc.issuer.currency;
  const periods = annualPeriods(doc).slice().reverse();
  const keys: [string, string, string][] = [
    ["revenue", "Revenue", C.muted],
    ["ebitda_proxy", "EBITDA", C.s1],
    ["fcf", "Free cash flow", C.s3],
  ];
  const data = keys.map(([k]) => periods.map((p) => (k === "revenue" ? fact(doc, p.id, k)?.value : metric(doc, p.id, k)?.value) ?? null));
  return (
    <Panel eyebrow={`${periods.length}-year profile · ${cur}`} title="Revenue, EBITDA & free cash flow"
      action={<Legend items={keys.map(([, l, c]) => [l, c])} />}>
      <EChart
        height={270}
        option={{
          grid: { left: 8, right: 8, top: 16, bottom: 4, containLabel: true },
          tooltip: { ...baseTooltip, valueFormatter: (v) => money(v as number, cur) },
          xAxis: { type: "category", data: periods.map((p) => p.id), ...axisCommon, splitLine: { show: false } },
          yAxis: { type: "value", ...axisCommon, axisLine: { show: false }, axisLabel: { ...axisCommon.axisLabel, formatter: axisMoney } },
          series: keys.map(([, l, c], i) => ({
            name: l, type: "bar", data: data[i], barMaxWidth: 34, barGap: "18%",
            itemStyle: { color: c, borderRadius: [4, 4, 0, 0] },
          })),
        }}
      />
    </Panel>
  );
}

export function Legend({ items }: { items: [string, string][] }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {items.map(([l, c]) => (
        <span key={l} className="inline-flex items-center gap-1.5 text-[11.5px] text-ink-3">
          <span className="size-2 rounded-[2px]" style={{ background: c }} /> {l}
        </span>
      ))}
    </div>
  );
}

function RiskCard({ onTab }: { onTab: (t: string) => void }) {
  const { doc } = useIssuerCtx();
  const rp = doc.risk_profile;
  const h = rp.headroom.leverage;
  const cf = rp.headroom.cashflow;
  return (
    <Panel eyebrow="Indicative financial risk profile" title={rp.label ?? "Not meaningful"}
      action={<button onClick={() => onTab("credit")} className="inline-flex items-center gap-1 text-[12px] text-amber hover:underline">Details <ArrowRight className="size-3" /></button>}>
      <div className="space-y-5">
        <TierLadder label="Net debt / EBITDA" value={rp.leverage.value} tier={rp.leverage.tier} kind="leverage" />
        <TierLadder label="CFO / net debt (FFO proxy)" value={rp.cashflow.value} tier={rp.cashflow.tier} kind="cashflow" />
        <div className="rounded-lg border border-hairline bg-panel-2 p-3.5 text-[13px] leading-relaxed text-ink-2">
          {rp.overall === null ? (
            <span>{rp.basis}</span>
          ) : h && h.ebitda_decline_to_downgrade !== null ? (
            <span>
              EBITDA could fall <b className="num text-ink-1">{pct(h.ebitda_decline_to_downgrade, 0)}</b> before net leverage crosses{" "}
              <b className="num text-ink-1">{times(h.next_threshold, 1)}</b> into <b className="text-ink-1">{TIERS[h.tier + 1]}</b>.
              {cf && cf.cfo_decline_to_downgrade !== null && (
                <> Operating cash flow could fall <b className="num text-ink-1">{pct(cf.cfo_decline_to_downgrade, 0)}</b> before CFO/debt drops below <b className="num text-ink-1">{pct(cf.next_threshold, 0)}</b>.</>
              )}
            </span>
          ) : rp.overall === 0 && rp.net_debt === 0 ? (
            <span>Cash and short-term investments exceed reported debt — a net-cash balance sheet sits in the strongest band.</span>
          ) : (
            <span>Already in the weakest band on at least one ratio. See the scenario lab for the path back.</span>
          )}
        </div>
        <p className="text-[11px] leading-relaxed text-ink-3">
          Thresholds from S&amp;P&apos;s public corporate methodology (standard volatility table). A financial-risk view only — not a credit rating.
        </p>
      </div>
    </Panel>
  );
}

function PeerPosition() {
  const { doc } = useIssuerCtx();
  const p = doc.peers;
  const rows: [string, string, "x" | "ratio"][] = [
    ["nlev", "Net debt / EBITDA", "x"], ["ecov", "EBITDA / interest", "x"], ["cfod", "CFO / debt", "ratio"],
    ["om", "Operating margin", "ratio"], ["g", "Revenue growth", "ratio"], ["cr", "Current ratio", "x"],
  ];
  const metricKey: Record<string, string> = { nlev: "net_leverage_adj", ecov: "ebitda_coverage", cfod: "cfo_to_debt", om: "operating_margin", g: "revenue_growth", cr: "current_ratio" };
  return (
    <Panel eyebrow={`vs ${p?.count ?? 0} ${p?.sector ?? ""} peers`} title="Peer position">
      <div className="space-y-3">
        {rows.map(([k, l, u]) => {
          const pc = p?.percentile?.[k];
          const med = p?.median?.[k];
          const v = metric(doc, doc.primary, metricKey[k])?.value ?? null;
          return (
            <div key={k}>
              <div className="flex items-baseline justify-between text-[12px]">
                <span className="text-ink-2">{l}</span>
                <span className="num text-ink-3">
                  <span className="text-ink-1">{k === "nlev" && v !== null && v <= 0 ? "net cash" : u === "x" ? times(v) : pct(v)}</span> · med {u === "x" ? times(med) : pct(med)}
                </span>
              </div>
              <div className="relative mt-1.5 h-1.5 rounded-full bg-panel-3">
                <div className="absolute inset-y-0 left-1/2 w-px bg-hairline-strong" />
                {pc !== undefined && (
                  <div className="absolute top-1/2 size-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-panel"
                    style={{ left: `${pc * 100}%`, background: pc >= 0.5 ? C.s1 : C.s2 }} />
                )}
              </div>
            </div>
          );
        })}
        <div className="flex justify-between pt-1 text-[10.5px] text-ink-3"><span>Weaker</span><span>Sector median</span><span>Stronger</span></div>
      </div>
    </Panel>
  );
}

function MemoTeaser({ onTab }: { onTab: (t: string) => void }) {
  const { doc } = useIssuerCtx();
  const claim = doc.memo?.en.overall_credit_view?.[0];
  return (
    <Panel eyebrow="AI credit memo · draft" title="Analyst view"
      action={<button onClick={() => onTab("memo")} className="inline-flex items-center gap-1 text-[12px] text-amber hover:underline">Read memo <ArrowRight className="size-3" /></button>}>
      {claim ? (
        <div className="flex h-full flex-col justify-between gap-4">
          <p className="relative pl-6 text-[13.5px] leading-relaxed text-ink-2">
            <Quote className="absolute left-0 top-0.5 size-4 text-amber/60" />
            {claim.text}
          </p>
          <div className="flex items-center gap-2 text-[11px] text-ink-3">
            <ShieldCheck className="size-3.5 text-good" />
            {claim.evidence.length} citations · unreviewed AI draft; open memo for consistency checks
          </div>
        </div>
      ) : (
        <p className="text-[13px] text-ink-3">No memo has been generated for this issuer yet. Open the memo tab to generate one.</p>
      )}
    </Panel>
  );
}

function Integrity({ onTab }: { onTab: (t: string) => void }) {
  const { doc } = useIssuerCtx();
  const f = doc.facts[doc.primary];
  const reported = Object.values(f).filter((x) => x.value !== null && x.status === "reported").length;
  const derived = Object.values(f).filter((x) => x.value !== null && x.status === "derived").length;
  const missing = Object.values(f).filter((x) => x.value === null).length;
  const restated = Object.values(f).reduce((a, x) => a + (x.restated > 0 ? 1 : 0), 0);
  return (
    <Panel eyebrow="Tick-and-tie" title="Data integrity"
      action={<button onClick={() => onTab("sources")} className="inline-flex items-center gap-1 text-[12px] text-amber hover:underline">Sources <ArrowRight className="size-3" /></button>}>
      <div className="grid grid-cols-3 gap-2 text-center">
        <Box n={reported} label="Agreed to filing" cls="text-amber" />
        <Box n={derived} label="Derived" cls="text-cyan" />
        <Box n={missing} label="N/A (not zero)" cls="text-ink-2" />
      </div>
      <ul className="mt-4 space-y-2 text-[12px] text-ink-2">
        <li className="flex items-center gap-2"><CircleCheck className="size-3.5 text-good" /> Debt scope: <span className="text-ink-1">{doc.debt_scope.completeness}</span></li>
        <li className="flex items-center gap-2"><CircleCheck className="size-3.5 text-good" /> {Object.keys(doc.sources).length} SEC facts linked to filings</li>
        {restated > 0 && <li className="flex items-center gap-2"><FileWarning className="size-3.5 text-warning" /> {restated} inputs restated in later filings (lineage kept)</li>}
      </ul>
    </Panel>
  );
}

function Box({ n, label, cls }: { n: number; label: string; cls: string }) {
  return (
    <div className="rounded-lg border border-hairline bg-panel-2 px-2 py-3">
      <div className={cn("num text-2xl font-semibold", cls)}>{n}</div>
      <div className="mt-1 text-[10.5px] text-ink-3">{label}</div>
    </div>
  );
}

function SectorPeers() {
  const { doc } = useIssuerCtx();
  const { data: u } = useUniverse();
  if (!u) return null;
  const me = u.issuers.find((r) => r.t === doc.issuer.ticker);
  const usd = (rev: number | null, cur: string) => (rev ?? 0) * (FX_SIZING[cur] ?? 0);
  const myRev = usd(fact(doc, doc.primary, "revenue")?.value ?? null, doc.issuer.currency);
  const peers = u.issuers
    .filter((r) => r.s === doc.issuer.sector && r.t !== doc.issuer.ticker && r.rev)
    .map((r) => ({ r, d: Math.abs(Math.log((usd(r.rev, r.cur) || 1) / (myRev || 1))) }))
    .sort((a, b) => a.d - b.d)
    .slice(0, 7)
    .map((x) => x.r)
    .sort((a, b) => usd(b.rev, b.cur) - usd(a.rev, a.cur));
  const rows = me ? [me, ...peers] : peers;
  return (
    <Panel eyebrow={`${doc.issuer.sector} · closest by revenue`} title="Sector peers" bodyClassName="p-0"
      action={<Link href="/screener" className="inline-flex items-center gap-1 text-[12px] text-amber hover:underline">Screener <ArrowRight className="size-3" /></Link>}>
      <div className="scrollbar-thin overflow-x-auto">
        <table className="w-full min-w-[760px] text-[12.5px]">
          <thead>
            <tr className="border-b border-hairline">
              {["Issuer", "Risk band", "Net debt/EBITDA", "EBITDA/int.", "CFO/debt", "Op. margin", "Rev. growth"].map((h, i) => (
                <th key={h} className={`label-caps px-4 py-2.5 font-normal ${i === 0 ? "text-left" : "text-right"}`}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const self = r.t === doc.issuer.ticker;
              return (
                <tr key={r.t} className={`border-b border-hairline/60 last:border-0 ${self ? "bg-amber/[0.06]" : "hover:bg-panel-2"}`}>
                  <td className="px-4 py-2">
                    <Link href={`/i/${r.t}`} className="flex items-center gap-2.5">
                      <span className={`num w-12 font-semibold ${self ? "text-amber" : "text-ink-1"}`}>{r.t}</span>
                      <span className="max-w-[260px] truncate text-ink-2">{titleCase(r.n)}</span>
                      {self && <span className="rounded bg-amber/15 px-1.5 text-[10px] text-amber">this issuer</span>}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-right"><TierChip tier={r.tier} compact /></td>
                  <td className="num px-4 py-2 text-right text-ink-1">{r.rlev === 0 ? "net cash" : times(r.rlev)}</td>
                  <td className="num px-4 py-2 text-right text-ink-1">{times(r.ecov, 1)}</td>
                  <td className="num px-4 py-2 text-right text-ink-1">{pct(r.cfod, 0)}</td>
                  <td className="num px-4 py-2 text-right text-ink-1">{pct(r.om, 1)}</td>
                  <td className="num px-4 py-2 text-right text-ink-1">{pct(r.g, 1, true)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
