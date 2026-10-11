"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowDown, ArrowUp, Download, Search, X } from "lucide-react";
import { Panel } from "@/components/common/panel";
import { TierChip } from "@/components/common/tier-chip";
import { EChart, C, axisCommon, baseTooltip } from "@/components/charts/echart";
import { FX_SIZING, pct, times, TIERS } from "@/lib/format";
import type { Universe, UniverseRow } from "@/lib/types";
import { cn } from "@/lib/utils";
import { titleCase } from "@/components/issuer/issuer-view";

type Col = { key: keyof UniverseRow; label: string; fmt: (r: UniverseRow) => string; better?: "up" | "down"; w?: string };
const COLS: Col[] = [
  { key: "tier", label: "Risk band", fmt: () => "" },
  { key: "rlev", label: "Net debt/EBITDA", fmt: (r) => (r.rlev === 0 ? "net cash" : times(r.rlev)), better: "down" },
  { key: "lev", label: "Debt/EBITDA", fmt: (r) => times(r.lev), better: "down" },
  { key: "ecov", label: "EBITDA/int.", fmt: (r) => times(r.ecov, 1), better: "up" },
  { key: "cfod", label: "CFO/debt", fmt: (r) => pct(r.cfod, 0), better: "up" },
  { key: "fcfd", label: "FCF/debt", fmt: (r) => pct(r.fcfd, 0), better: "up" },
  { key: "om", label: "Op. margin", fmt: (r) => pct(r.om, 1), better: "up" },
  { key: "g", label: "Rev. growth", fmt: (r) => pct(r.g, 1, true), better: "up" },
  { key: "hd", label: "Headroom", fmt: (r) => pct(r.hd, 0), better: "up" },
  { key: "z", label: "Altman Z″", fmt: (r) => (r.z === null ? "N/A" : r.z.toFixed(2)), better: "up" },
];

export function Screener({ u }: { u: Universe }) {
  const router = useRouter();
  const sectors = useMemo(() => Array.from(new Set(u.issuers.map((r) => r.s))).sort(), [u]);
  const [q, setQ] = useState("");
  const [sector, setSector] = useState<string>("All");
  const [tiers, setTiers] = useState<Set<number>>(new Set());
  const [hkOnly, setHkOnly] = useState(false);
  const [usdOnly, setUsdOnly] = useState(false);
  const [sort, setSort] = useState<{ key: keyof UniverseRow; dir: 1 | -1 }>({ key: "rank", dir: 1 });

  const rows = useMemo(() => {
    const Q = q.trim().toUpperCase();
    const list = u.issuers.filter((r) =>
      (!Q || r.t.includes(Q) || r.n.toUpperCase().includes(Q)) &&
      (sector === "All" || r.s === sector) &&
      (!tiers.size || (r.tier !== null && tiers.has(r.tier))) &&
      (!hkOnly || r.hk) && (!usdOnly || r.cur === "USD"));
    const k = sort.key;
    return list.sort((a, b) => {
      const va = a[k] as number | null, vb = b[k] as number | null;
      if (va === null && vb === null) return 0;
      if (va === null) return 1;
      if (vb === null) return -1;
      return (va > vb ? 1 : va < vb ? -1 : 0) * sort.dir;
    });
  }, [u, q, sector, tiers, hkOnly, usdOnly, sort]);

  // Column-wise percentile for subtle heat shading (better = stronger blue).
  const ranks = useMemo(() => {
    const out: Record<string, Map<string, number>> = {};
    for (const c of COLS) {
      if (!c.better) continue;
      const vals = u.issuers.filter((r) => r[c.key] !== null).map((r) => ({ t: r.t, v: r[c.key] as number })).sort((a, b) => a.v - b.v);
      const m = new Map<string, number>();
      vals.forEach((x, i) => m.set(x.t, c.better === "up" ? i / (vals.length - 1) : 1 - i / (vals.length - 1)));
      out[c.key as string] = m;
    }
    return out;
  }, [u]);

  const scatter = rows.filter((r) => r.rlev !== null && r.ecov !== null && r.tier !== null);
  const toggleTier = (i: number) => setTiers((s) => { const n = new Set(s); if (n.has(i)) n.delete(i); else n.add(i); return n; });
  const setSortKey = (key: keyof UniverseRow) => setSort((s) => ({ key, dir: s.key === key ? ((-s.dir) as 1 | -1) : (key === "rank" || key === "t" ? 1 : -1) }));

  const exportCsv = () => {
    const head = ["ticker", "name", "sector", "currency", "fiscal_year", "risk_band", ...COLS.slice(1).map((c) => c.label)];
    const lines = rows.map((r) => [r.t, `"${r.n}"`, r.s, r.cur, r.fy, r.tier === null ? "" : TIERS[r.tier], ...COLS.slice(1).map((c) => r[c.key] ?? "")].join(","));
    const blob = new Blob([[head.join(","), ...lines].join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "tickmark-screener.csv";
    a.click();
  };

  return (
    <div className="mx-auto max-w-[1480px] space-y-4 px-4 pb-20 pt-6 sm:px-6">
      <div className="flex flex-col gap-1">
        <div className="label-caps">Screener · {u.count} issuers · latest fiscal year</div>
        <h1 className="text-[26px] font-semibold tracking-tight text-ink-1">Compare credit profiles across the universe</h1>
      </div>
      <div className="panel flex flex-wrap items-center gap-2 p-3">
        <label className="flex h-9 min-w-[220px] flex-1 items-center gap-2 rounded-lg border border-hairline-strong bg-panel-2 px-3 sm:flex-none">
          <Search className="size-4 text-ink-3" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ticker or name" className="w-full bg-transparent text-[13px] text-ink-1 outline-none placeholder:text-ink-3" />
        </label>
        <select value={sector} onChange={(e) => setSector(e.target.value)}
          className="h-9 rounded-lg border border-hairline-strong bg-panel-2 px-3 text-[13px] text-ink-1 outline-none">
          <option>All</option>
          {sectors.map((s) => <option key={s}>{s}</option>)}
        </select>
        <div className="flex flex-wrap items-center gap-1.5">
          {TIERS.map((t, i) => (
            <button key={t} onClick={() => toggleTier(i)} className={cn("rounded-full transition-opacity", tiers.size && !tiers.has(i) && "opacity-35")}>
              <TierChip tier={i} compact />
            </button>
          ))}
        </div>
        <Toggle on={hkOnly} onClick={() => setHkOnly(!hkOnly)}>HK dual-listed</Toggle>
        <Toggle on={usdOnly} onClick={() => setUsdOnly(!usdOnly)}>USD reporters</Toggle>
        {(q || sector !== "All" || tiers.size || hkOnly || usdOnly) ? (
          <button onClick={() => { setQ(""); setSector("All"); setTiers(new Set()); setHkOnly(false); setUsdOnly(false); }}
            className="inline-flex items-center gap-1 text-[12px] text-ink-3 hover:text-ink-1"><X className="size-3.5" /> Clear</button>
        ) : null}
        <span className="num ml-auto text-[12px] text-ink-3">{rows.length} shown</span>
      </div>

      <Panel eyebrow="Each dot is an issuer · colour = indicative risk band · size = revenue (approx. USD)" title="Leverage vs. interest cover"
        action={<span className="hidden text-[11.5px] text-ink-3 sm:inline">Bottom-right = weaker · click a dot to open</span>}>
        <EChart
          height={420}
          onEvents={{ click: (p: unknown) => { const d = (p as { data: { t: string } }).data; if (d?.t) router.push(`/i/${d.t}`); } }}
          option={{
            grid: { left: 12, right: 24, top: 34, bottom: 30, containLabel: true },
            tooltip: { ...baseTooltip, trigger: "item", formatter: (p: unknown) => {
              const d = (p as { data: { t: string; n: string; value: number[]; tier: number } }).data;
              return `<b>${d.t}</b> · ${titleCase(d.n)}<br/>Net debt/EBITDA <b>${d.value[0].toFixed(2)}x</b> · EBITDA/interest <b>${d.value[1].toFixed(1)}x</b><br/>${TIERS[d.tier]}`;
            } },
            xAxis: { type: "value", min: 0, max: 7, name: "Net debt / EBITDA (x) →", nameLocation: "middle", nameGap: 28, nameTextStyle: { color: C.ink3, fontSize: 11 }, ...axisCommon,
              axisLabel: { ...axisCommon.axisLabel, formatter: (v: number) => `${v}x` } },
            yAxis: { type: "log", min: 0.5, max: 200, logBase: 10, name: "EBITDA / interest (x, log scale)", nameGap: 14, nameTextStyle: { color: C.ink3, fontSize: 11, align: "left" }, ...axisCommon,
              axisLabel: { ...axisCommon.axisLabel, formatter: (v: number) => `${v}x` } },
            series: [{
              type: "scatter",
              data: scatter.map((r) => ({
                t: r.t, n: r.n, tier: r.tier,
                value: [Math.min(r.rlev!, 7), Math.max(0.5, Math.min(r.ecov!, 200))],
                symbolSize: Math.max(6, Math.min(30, Math.sqrt(((r.rev ?? 0) * (FX_SIZING[r.cur] ?? 0)) / 1e9) * 2.1)),
                itemStyle: { color: C.tiers[r.tier!], opacity: 0.82, borderColor: "#06080b", borderWidth: 1 },
              })),
              emphasis: { scale: 1.4, itemStyle: { opacity: 1, borderColor: "#fff" } },
              markLine: { silent: true, symbol: "none", lineStyle: { color: "#283340", type: "dashed" }, label: { color: C.ink3, fontSize: 10, formatter: "{b}" },
                data: [{ xAxis: 3, name: "3x" }, { yAxis: 3, name: "3x cover" }] },
            }],
          }}
        />
      </Panel>

      <Panel eyebrow="Click headers to sort · shading = percentile within the universe (bluer = stronger)" title="All issuers" bodyClassName="p-0"
        action={<button onClick={exportCsv} className="inline-flex items-center gap-1.5 rounded-md border border-hairline-strong px-2.5 py-1 text-[12px] text-ink-2 hover:text-ink-1"><Download className="size-3.5" /> CSV</button>}>
        <div className="scrollbar-thin max-h-[720px] overflow-auto">
          <table className="w-full min-w-[1100px] text-[12.5px]">
            <thead className="sticky top-0 z-10 bg-panel">
              <tr className="border-b border-hairline">
                <Th onClick={() => setSortKey("t")} active={sort.key === "t"} dir={sort.dir} left>Issuer</Th>
                <Th onClick={() => setSortKey("s")} active={sort.key === "s"} dir={sort.dir} left>Sector</Th>
                {COLS.map((c) => <Th key={c.key as string} onClick={() => setSortKey(c.key)} active={sort.key === c.key} dir={sort.dir}>{c.label}</Th>)}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.t} className="border-b border-hairline/50 hover:bg-panel-2">
                  <td className="px-4 py-1.5">
                    <Link href={`/i/${r.t}`} className="flex items-center gap-2.5">
                      <span className="num w-12 shrink-0 font-semibold text-amber">{r.t}</span>
                      <span className="max-w-[220px] truncate text-ink-1">{titleCase(r.n)}</span>
                      {r.hk && <span className="num rounded bg-panel-3 px-1 text-[10px] text-ink-3">HK</span>}
                      {r.cur !== "USD" && <span className="num text-[10px] text-ink-3">{r.cur}</span>}
                    </Link>
                  </td>
                  <td className="whitespace-nowrap px-3 py-1.5 text-ink-3">{r.s}</td>
                  {COLS.map((c) => {
                    if (c.key === "tier") return <td key="tier" className="px-3 py-1.5 text-right"><TierChip tier={r.tier} compact /></td>;
                    const p = ranks[c.key as string]?.get(r.t);
                    return (
                      <td key={c.key as string} className="num px-3 py-1.5 text-right"
                        style={{ background: p === undefined ? undefined : `rgba(57,135,229,${(p * 0.22).toFixed(3)})`, color: r[c.key] === null ? "var(--ink-3)" : undefined }}>
                        {c.fmt(r)}
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

function Th({ children, onClick, active, dir, left }: { children: React.ReactNode; onClick: () => void; active: boolean; dir: 1 | -1; left?: boolean }) {
  return (
    <th className={cn("label-caps cursor-pointer select-none whitespace-nowrap px-3 py-2.5 font-normal hover:text-ink-1", left ? "text-left" : "text-right", active && "text-amber")} onClick={onClick}>
      <span className="inline-flex items-center gap-1">{children}{active && (dir === 1 ? <ArrowUp className="size-3" /> : <ArrowDown className="size-3" />)}</span>
    </th>
  );
}

function Toggle({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick} className={cn("h-9 rounded-lg border px-3 text-[12.5px] transition-colors", on ? "border-amber/50 bg-amber/10 text-amber" : "border-hairline-strong bg-panel-2 text-ink-2 hover:text-ink-1")}>
      {children}
    </button>
  );
}
