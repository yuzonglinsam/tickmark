"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Flame, Landmark, Search, ShieldAlert, Timer } from "lucide-react";
import { Panel } from "@/components/common/panel";
import { TierChip } from "@/components/common/tier-chip";
import { EChart, C, baseTooltip } from "@/components/charts/echart";
import { openCommandMenu } from "@/components/shell/command-menu";
import { FX_SIZING, money, pct, times, TIERS, tierColor } from "@/lib/format";
import type { Universe, UniverseRow } from "@/lib/types";
import { titleCase } from "@/components/issuer/issuer-view";

export function TerminalHome({ u }: { u: Universe }) {
  const router = useRouter();
  const rows = u.issuers;
  const memoCount = rows.filter((r) => r.memo).length;
  const usd = (r: UniverseRow) => (r.rev ?? 0) * (FX_SIZING[r.cur] ?? 0);

  const tierCounts = TIERS.map((_, i) => rows.filter((r) => r.tier === i).length);
  const nm = rows.filter((r) => r.tier === null).length;

  const treemap = useMemo(() => {
    const bySector = new Map<string, UniverseRow[]>();
    rows.forEach((r) => bySector.set(r.s, [...(bySector.get(r.s) ?? []), r]));
    return Array.from(bySector.entries()).map(([s, items]) => ({
      name: s,
      children: items.filter((r) => usd(r) > 0).map((r) => ({
        name: r.t, value: usd(r), tier: r.tier, full: r.n, lev: r.rlev,
        itemStyle: { color: r.tier === null ? "#2a333f" : C.tiers[r.tier], borderColor: "#06080b" },
      })),
    }));
  }, [rows]);

  const tight = rows.filter((r) => r.hd !== null && r.tier !== null && r.tier < 5).sort((a, b) => a.hd! - b.hd!).slice(0, 8);
  const levered = rows.filter((r) => r.rlev !== null && r.tier !== null).sort((a, b) => b.rlev! - a.rlev!).slice(0, 8);
  const payouts = rows.filter((r) => r.srf !== null && r.srf > 1).sort((a, b) => b.srf! - a.srf!).slice(0, 8);
  const hk = rows.filter((r) => r.hk).sort((a, b) => (a.rank ?? 0) - (b.rank ?? 0));
  const tape = rows.filter((r) => r.tier !== null).slice(0, 60);

  return (
    <div className="pb-20">
      <div className="overflow-hidden border-b border-hairline bg-panel/60">
        <div className="marquee flex w-max gap-8 py-2">
          {[...tape, ...tape].map((r, i) => (
            <Link key={i} href={`/i/${r.t}`} className="num flex items-center gap-2 text-[11.5px] text-ink-3 hover:text-ink-1">
              <span className="font-semibold text-ink-2">{r.t}</span>
              <span>{r.rlev === 0 ? "net cash" : times(r.rlev)}</span>
              <span style={{ color: tierColor(r.tier) }}>{TIERS[r.tier!]}</span>
            </Link>
          ))}
        </div>
      </div>
      <div className="mx-auto max-w-[1480px] space-y-4 px-4 pt-6 sm:px-6">
        <section className="relative overflow-hidden rounded-2xl border border-hairline bg-panel p-6 sm:p-8">
          <div className="grid-bg pointer-events-none absolute inset-0 opacity-50 [mask-image:radial-gradient(70%_80%_at_80%_0%,black,transparent)]" />
          <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="label-caps">Credit terminal · {u.generated_at.slice(0, 10)}</div>
              <h1 className="mt-2 text-[28px] font-semibold tracking-tight text-ink-1 sm:text-[34px]">
                {u.count} issuers. Every number <span className="text-amber">ticks to its filing.</span>
              </h1>
              <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-ink-2">
                Large-cap US-listed non-financial companies plus Hong Kong dual-listed China issuers, normalised from SEC XBRL.
                Search any of 10,000+ SEC filers for a live analysis.
              </p>
            </div>
            <button onClick={openCommandMenu}
              className="flex h-12 w-full max-w-[420px] items-center gap-3 rounded-xl border border-amber/40 bg-amber/5 px-4 text-left text-[14px] text-ink-2 transition-colors hover:bg-amber/10">
              <Search className="size-4 text-amber" /> Search a company or ticker…
              <kbd className="num ml-auto rounded border border-hairline-strong px-1.5 py-0.5 text-[10px] text-ink-3">⌘K</kbd>
            </button>
          </div>
          <div className="relative mt-7 grid grid-cols-2 gap-4 border-t border-hairline pt-6 md:grid-cols-4">
            <Kpi label="Issuers covered" value={String(u.count)} sub={`${hk.length} HK dual-listed`} />
            <Kpi label="AI memos (EN + 繁中)" value={String(memoCount)} sub="cited, digit-free drafts" />
            <Kpi label="Net-cash balance sheets" value={String(rows.filter((r) => r.nd === 0).length)} sub="cash ≥ reported debt" />
            <Kpi label="Payouts above FCF" value={String(rows.filter((r) => r.srf !== null && r.srf > 1).length)} sub="dividends + buybacks > FCF" />
          </div>
        </section>

        <div className="grid gap-4 xl:grid-cols-[1.7fr_1fr]">
          <Panel eyebrow="Tile size = revenue (approx. USD) · colour = indicative risk band" title="Universe map"
            action={<div className="hidden flex-wrap gap-2 sm:flex">{TIERS.map((t, i) => (
              <span key={t} className="inline-flex items-center gap-1 text-[10.5px] text-ink-3"><span className="size-2 rounded-sm" style={{ background: C.tiers[i] }} />{t}</span>))}</div>}>
            <EChart
              height={600}
              onEvents={{ click: (p: unknown) => { const d = (p as { data?: { name?: string; full?: string } }).data; if (d?.full) router.push(`/i/${d.name}`); } }}
              option={{
                tooltip: { ...baseTooltip, trigger: "item", formatter: (p: unknown) => {
                  const d = (p as { data: { name: string; full?: string; tier?: number | null; lev?: number | null } }).data;
                  if (!d.full) return `<b>${d.name}</b>`;
                  return `<b>${d.name}</b> · ${titleCase(d.full)}<br/>${d.tier === null || d.tier === undefined ? "Not meaningful" : TIERS[d.tier]} · net leverage ${d.lev === 0 ? "net cash" : times(d.lev ?? null)}`;
                } },
                series: [{
                  type: "treemap", data: treemap, roam: false, nodeClick: false, breadcrumb: { show: false },
                  width: "100%", height: "100%", top: 0, left: 0, right: 0, bottom: 0,
                  label: { show: true, formatter: "{b}", color: "#06080b", fontSize: 11, fontWeight: 600, fontFamily: "JetBrains Mono Variable" },
                  upperLabel: { show: true, height: 20, color: C.ink2, fontSize: 10.5, fontFamily: "Inter Variable", backgroundColor: "#0b0f14" },
                  itemStyle: { borderColor: "#06080b", borderWidth: 1, gapWidth: 1 },
                  levels: [{ itemStyle: { borderColor: "#0b0f14", borderWidth: 3, gapWidth: 3 } }, { itemStyle: { gapWidth: 1 } }],
                }],
              }}
            />
          </Panel>
          <div className="space-y-4">
            <Panel eyebrow={`${u.count - nm} issuers with a meaningful profile`} title="Risk band distribution">
              <div className="space-y-2.5">
                {TIERS.map((t, i) => (
                  <div key={t} className="flex items-center gap-3">
                    <span className="w-28 shrink-0 text-[12px] text-ink-2">{t}</span>
                    <div className="h-5 flex-1 overflow-hidden rounded bg-panel-3">
                      <div className="h-full rounded" style={{ width: `${(tierCounts[i] / Math.max(...tierCounts)) * 100}%`, background: C.tiers[i], opacity: 0.85 }} />
                    </div>
                    <span className="num w-9 text-right text-[12px] text-ink-1">{tierCounts[i]}</span>
                  </div>
                ))}
                <div className="flex items-center gap-3 text-ink-3">
                  <span className="w-28 shrink-0 text-[12px]">Not meaningful</span>
                  <div className="h-5 flex-1 overflow-hidden rounded bg-panel-3"><div className="h-full rounded bg-ink-3/30" style={{ width: `${(nm / Math.max(...tierCounts)) * 100}%` }} /></div>
                  <span className="num w-9 text-right text-[12px]">{nm}</span>
                </div>
              </div>
            </Panel>
            <Panel eyebrow="Median net debt / EBITDA by sector" title="Sector leverage" bodyClassName="p-0">
              <SectorTable u={u} />
            </Panel>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <List title="Tightest headroom" eyebrow="EBITDA decline to next band" icon={<Timer className="size-4 text-serious" />} rows={tight}
            value={(r) => pct(r.hd, (r.hd ?? 1) < 0.1 ? 1 : 0)} />
          <List title="Most leveraged" eyebrow="Net debt / EBITDA" icon={<Flame className="size-4 text-critical" />} rows={levered}
            value={(r) => times(r.rlev)} />
          <List title="Paying out more than FCF" eyebrow="Dividends + buybacks / FCF" icon={<ShieldAlert className="size-4 text-warning" />} rows={payouts}
            value={(r) => `${(r.srf ?? 0).toFixed(1)}x FCF`} />
          <List title="Hong Kong dual-listed" eyebrow="US ADS + HKEX listing" icon={<Landmark className="size-4 text-amber" />} rows={hk.slice(0, 8)}
            value={(r) => `HK ${r.hk}`} />
        </div>
      </div>
    </div>
  );
}

function Kpi({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div>
      <div className="label-caps">{label}</div>
      <div className="num mt-1.5 text-[28px] font-semibold tracking-tight text-ink-1">{value}</div>
      <div className="text-[12px] text-ink-3">{sub}</div>
    </div>
  );
}

function List({ title, eyebrow, icon, rows, value }: { title: string; eyebrow: string; icon: React.ReactNode; rows: UniverseRow[]; value: (r: UniverseRow) => string }) {
  return (
    <Panel eyebrow={eyebrow} title={<span className="flex items-center gap-2">{icon}{title}</span>} bodyClassName="p-2">
      <ul>
        {rows.map((r) => (
          <li key={r.t}>
            <Link href={`/i/${r.t}`} className="group flex items-center gap-3 rounded-md px-3 py-2 hover:bg-panel-2">
              <span className="num w-12 shrink-0 text-[12.5px] font-semibold text-amber">{r.t}</span>
              <span className="min-w-0 flex-1 truncate text-[12.5px] text-ink-2">{titleCase(r.n)}</span>
              <span className="num text-[12.5px] text-ink-1">{value(r)}</span>
              <ArrowRight className="size-3.5 text-ink-3 opacity-0 transition-opacity group-hover:opacity-100" />
            </Link>
          </li>
        ))}
      </ul>
    </Panel>
  );
}

function SectorTable({ u }: { u: Universe }) {
  const rows = Object.entries(u.sectors)
    .filter(([, s]) => (s.count as number) >= 5)
    .map(([name, s]) => ({ name, count: s.count as number, nlev: (s.nlev as { median: number } | undefined)?.median ?? null, om: (s.om as { median: number } | undefined)?.median ?? null }))
    .sort((a, b) => (b.nlev ?? 0) - (a.nlev ?? 0));
  const max = Math.max(...rows.map((r) => r.nlev ?? 0), 1);
  return (
    <table className="w-full text-[12px]">
      <tbody>
        {rows.map((r) => (
          <tr key={r.name} className="border-b border-hairline/60 last:border-0">
            <td className="px-5 py-2 text-ink-2">{r.name} <span className="text-ink-3">· {r.count}</span></td>
            <td className="w-[40%] px-2 py-2">
              <div className="h-1.5 overflow-hidden rounded-full bg-panel-3"><div className="h-full rounded-full bg-series-1" style={{ width: `${((r.nlev ?? 0) / max) * 100}%` }} /></div>
            </td>
            <td className="num px-5 py-2 text-right text-ink-1">{times(r.nlev)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export { money, TierChip };
