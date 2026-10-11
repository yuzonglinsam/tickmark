"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Command as Cmdk } from "cmdk";
import { ArrowRight, BookOpen, LayoutGrid, Radar, Search, Sparkles, Zap } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { useTickers, useUniverse } from "@/lib/data";
import { TierChip } from "@/components/common/tier-chip";
import type { UniverseRow } from "@/lib/types";

export const openCommandMenu = () => window.dispatchEvent(new Event("tickmark:open-search"));

const FEATURED = ["KO", "BA", "BABA", "AAPL", "CCL", "NIO", "ORCL", "INTC"];

function rank(q: string, ticker: string, name: string): number | null {
  const t = ticker.toUpperCase();
  const Q = q.toUpperCase();
  if (t === Q) return 0;
  if (t.startsWith(Q)) return 1 + t.length / 100;
  const n = name.toUpperCase();
  if (n.startsWith(Q)) return 2;
  if (Q.length >= 2 && n.includes(Q)) return 3;
  return null;
}

export function CommandMenu() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const router = useRouter();
  const { data: universe } = useUniverse();
  const { data: tickers } = useTickers(open);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !isTyping(e))) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    const onOpen = () => setOpen(true);
    window.addEventListener("keydown", onKey);
    window.addEventListener("tickmark:open-search", onOpen);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("tickmark:open-search", onOpen);
    };
  }, []);

  const covered = useMemo(() => new Map((universe?.issuers ?? []).map((r) => [r.t, r])), [universe]);

  const results = useMemo(() => {
    const query = q.trim();
    if (!query) return { covered: FEATURED.map((t) => covered.get(t)).filter(Boolean) as UniverseRow[], live: [] };
    const cov = (universe?.issuers ?? [])
      .map((r) => ({ r, s: rank(query, r.t, r.n) }))
      .filter((x) => x.s !== null)
      .sort((a, b) => a.s! - b.s! || (a.r.rank ?? 9999) - (b.r.rank ?? 9999))
      .slice(0, 8)
      .map((x) => x.r);
    const live = (tickers ?? [])
      .filter(([t]) => !covered.has(t))
      .map((row) => ({ row, s: rank(query, row[0], row[1]) }))
      .filter((x) => x.s !== null)
      .sort((a, b) => a.s! - b.s!)
      .slice(0, 6)
      .map((x) => x.row);
    return { covered: cov, live };
  }, [q, universe, tickers, covered]);

  const go = (href: string) => {
    setOpen(false);
    setQ("");
    router.push(href);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent
        showCloseButton={false}
        className="top-[18%] translate-y-0 overflow-hidden border-hairline-strong bg-popover p-0 shadow-2xl shadow-black/60 sm:max-w-[640px]"
      >
        <DialogTitle className="sr-only">Search issuers</DialogTitle>
        <DialogDescription className="sr-only">Search covered issuers or any SEC filer</DialogDescription>
        <Cmdk shouldFilter={false} className="flex flex-col" loop>
          <div className="flex items-center gap-3 border-b border-hairline px-4">
            <Search className="size-4 text-ink-3" />
            <Cmdk.Input
              value={q}
              onValueChange={setQ}
              autoFocus
              placeholder="Search 10,000+ SEC filers by ticker or company…"
              className="h-14 flex-1 bg-transparent text-[15px] text-ink-1 outline-none placeholder:text-ink-3"
            />
            <kbd className="num rounded border border-hairline-strong px-1.5 py-0.5 text-[10px] text-ink-3">ESC</kbd>
          </div>
          <Cmdk.List className="scrollbar-thin max-h-[420px] overflow-y-auto p-2">
            <Cmdk.Empty className="px-3 py-10 text-center text-sm text-ink-3">
              No SEC filer matches “{q}”.
            </Cmdk.Empty>
            {!q && (
              <Cmdk.Group heading="Navigate" className="cmdk-group">
                <Item onSelect={() => go("/terminal")} icon={<Radar className="size-4" />} label="Terminal home" hint="Market overview" />
                <Item onSelect={() => go("/screener")} icon={<LayoutGrid className="size-4" />} label="Screener" hint="Compare 490+ issuers" />
                <Item onSelect={() => go("/methodology")} icon={<BookOpen className="size-4" />} label="Methodology" hint="Formulas & limits" />
              </Cmdk.Group>
            )}
            {results.covered.length > 0 && (
              <Cmdk.Group heading={q ? "Covered issuers · instant" : "Featured issuers"} className="cmdk-group">
                {results.covered.map((r) => (
                  <Cmdk.Item
                    key={r.t}
                    value={`cov-${r.t}`}
                    onSelect={() => go(`/i/${r.t}`)}
                    className="group flex cursor-pointer items-center gap-3 rounded-md px-3 py-2.5 data-[selected=true]:bg-accent"
                  >
                    <span className="num w-16 shrink-0 text-[13px] font-semibold text-amber">{r.t}</span>
                    <span className="min-w-0 flex-1 truncate text-[13.5px] text-ink-1">{r.n}</span>
                    {r.hk && <span className="num rounded bg-panel-3 px-1.5 py-0.5 text-[10px] text-ink-2">HK {r.hk}</span>}
                    <span className="hidden text-[11px] text-ink-3 sm:inline">{r.s}</span>
                    <TierChip tier={r.tier} compact />
                    <ArrowRight className="size-3.5 text-ink-3 opacity-0 group-data-[selected=true]:opacity-100" />
                  </Cmdk.Item>
                ))}
              </Cmdk.Group>
            )}
            {results.live.length > 0 && (
              <Cmdk.Group heading="Any SEC filer · live analysis (~10s)" className="cmdk-group">
                {results.live.map(([t, n]) => (
                  <Cmdk.Item
                    key={t}
                    value={`live-${t}`}
                    onSelect={() => go(`/i/${t}`)}
                    className="group flex cursor-pointer items-center gap-3 rounded-md px-3 py-2.5 data-[selected=true]:bg-accent"
                  >
                    <span className="num w-16 shrink-0 text-[13px] font-semibold text-ink-2">{t}</span>
                    <span className="min-w-0 flex-1 truncate text-[13.5px] text-ink-2">{n}</span>
                    <span className="inline-flex items-center gap-1 rounded border border-cyan/30 px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-cyan">
                      <Zap className="size-3" /> LIVE
                    </span>
                  </Cmdk.Item>
                ))}
              </Cmdk.Group>
            )}
          </Cmdk.List>
          <div className="flex items-center justify-between border-t border-hairline px-4 py-2 text-[11px] text-ink-3">
            <span className="inline-flex items-center gap-1.5">
              <Sparkles className="size-3 text-amber" /> Covered issuers load instantly; others are computed live from SEC EDGAR.
            </span>
            <span className="num hidden sm:inline">↑↓ ↵</span>
          </div>
        </Cmdk>
      </DialogContent>
    </Dialog>
  );
}

function Item({ onSelect, icon, label, hint }: { onSelect: () => void; icon: React.ReactNode; label: string; hint: string }) {
  return (
    <Cmdk.Item
      value={`nav-${label}`}
      onSelect={onSelect}
      className="flex cursor-pointer items-center gap-3 rounded-md px-3 py-2.5 text-ink-2 data-[selected=true]:bg-accent data-[selected=true]:text-ink-1"
    >
      {icon}
      <span className="text-[13.5px]">{label}</span>
      <span className="ml-auto text-[11px] text-ink-3">{hint}</span>
    </Cmdk.Item>
  );
}

function isTyping(e: KeyboardEvent) {
  const el = e.target as HTMLElement | null;
  return !!el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable);
}
