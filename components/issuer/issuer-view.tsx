"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowUpRight, Building2, Loader2, MessageSquareText, TriangleAlert, Zap } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useIssuer } from "@/lib/data";
import { fmtDate, titleCase } from "@/lib/format";
import type { Issuer } from "@/lib/types";
import { TierChip } from "@/components/common/tier-chip";
import { IssuerProvider, useIssuerCtx } from "./source-context";
import { SourceDrawer } from "./source-drawer";
import { Overview } from "./overview";
import { CreditProfile } from "./credit-profile";
import { ScenarioLab } from "./scenario-lab";
import { DebtLiquidity } from "./debt-liquidity";
import { CashFlow } from "./cash-flow";
import { MemoTab } from "./memo";
import { SourcesTab } from "./sources";
import { AskPanel } from "./ask-panel";

const TABS = [
  ["overview", "Overview"],
  ["credit", "Credit profile"],
  ["scenario", "Scenario lab"],
  ["debt", "Debt & liquidity"],
  ["cash", "Cash flow"],
  ["memo", "AI memo"],
  ["sources", "Sources"],
] as const;

export function IssuerView({ ticker, covered }: { ticker: string; covered: boolean }) {
  const { data, error, loading } = useIssuer(ticker, covered);
  if (error) return <LoadError ticker={ticker} error={error} />;
  if (!data || loading) return <LoadingState ticker={ticker} live={covered === false} />;
  return (
    <IssuerProvider key={data.issuer.ticker} doc={data}>
      <IssuerBody />
    </IssuerProvider>
  );
}

function IssuerBody() {
  const { doc, setAskOpen } = useIssuerCtx();
  // IssuerBody only mounts client-side (after data loads), so reading the hash here is safe.
  const [tab, setTab] = useState<string>(() => {
    const h = typeof window === "undefined" ? "" : window.location.hash.replace("#", "");
    return TABS.some(([k]) => k === h) ? h : "overview";
  });
  const change = (v: string) => {
    setTab(v);
    history.replaceState(null, "", `#${v}`);
  };
  // Terminal-style keys: 1–7 switch tabs, A opens Ask.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement | null;
      if (e.metaKey || e.ctrlKey || e.altKey || (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable))) return;
      if (document.querySelector("[role=dialog]")) return;
      const n = Number(e.key);
      if (n >= 1 && n <= TABS.length) { change(TABS[n - 1][0]); }
      else if (e.key === "a" || e.key === "A") { e.preventDefault(); setAskOpen(true); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <div className="mx-auto w-full max-w-[1480px] px-4 pb-24 sm:px-6">
      <Header doc={doc} onAsk={() => setAskOpen(true)} />
      <Tabs value={tab} onValueChange={change} className="mt-5 gap-5">
        <div className="scrollbar-thin -mx-4 flex items-center overflow-x-auto border-b border-hairline px-4 sm:mx-0 sm:px-0">
          <TabsList className="h-auto gap-1 rounded-none bg-transparent p-0">
            {TABS.map(([k, l]) => (
              <TabsTrigger
                key={k}
                value={k}
                className="relative h-10 flex-none rounded-none border-0 bg-transparent px-3 focus-visible:outline-none focus-visible:ring-0 focus-visible:text-amber dark:data-[state=active]:bg-transparent text-[13px] text-ink-3 shadow-none hover:text-ink-1 data-[state=active]:bg-transparent data-[state=active]:text-ink-1 data-[state=active]:shadow-none data-[state=active]:after:absolute data-[state=active]:after:inset-x-2 data-[state=active]:after:-bottom-px data-[state=active]:after:h-[2px] data-[state=active]:after:rounded-full data-[state=active]:after:bg-amber"
              >
                {l}
                {k === "memo" && doc.memo && <span className="ml-1.5 size-1.5 rounded-full bg-amber" />}
              </TabsTrigger>
            ))}
          </TabsList>
          <span className="num ml-auto hidden items-center gap-2 pr-1 text-[10.5px] text-ink-3 xl:flex">
            <kbd className="rounded border border-hairline-strong px-1">1</kbd>–<kbd className="rounded border border-hairline-strong px-1">7</kbd> tabs
            <kbd className="ml-2 rounded border border-hairline-strong px-1">A</kbd> ask
          </span>
        </div>
        <TabsContent value="overview"><Overview onTab={change} /></TabsContent>
        <TabsContent value="credit"><CreditProfile /></TabsContent>
        <TabsContent value="scenario"><ScenarioLab /></TabsContent>
        <TabsContent value="debt"><DebtLiquidity /></TabsContent>
        <TabsContent value="cash"><CashFlow /></TabsContent>
        <TabsContent value="memo"><MemoTab /></TabsContent>
        <TabsContent value="sources"><SourcesTab /></TabsContent>
      </Tabs>
      <SourceDrawer />
      <AskPanel />
    </div>
  );
}

function Header({ doc, onAsk }: { doc: Issuer; onAsk: () => void }) {
  const i = doc.issuer;
  const annual = doc.filings.annual;
  const rp = doc.risk_profile;
  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="relative mt-6 overflow-hidden rounded-2xl border border-hairline bg-panel"
    >
      <div className="glow-amber pointer-events-none absolute inset-0 opacity-60" />
      <div className="grid-bg pointer-events-none absolute inset-0 opacity-40 [mask-image:linear-gradient(to_bottom,black,transparent)]" />
      <div className="relative flex flex-col gap-5 p-5 sm:p-7 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0 lg:flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="num rounded-md bg-amber px-2 py-0.5 text-[13px] font-bold text-primary-foreground">{i.ticker}</span>
            {i.exchange && <span className="num text-[11.5px] text-ink-3">{i.exchange}</span>}
            {i.hk && (
              <span className="num rounded-md border border-hairline-strong px-1.5 py-0.5 text-[11px] text-ink-2">
                HKEX {i.hk}
              </span>
            )}
            {doc.live && (
              <span className="inline-flex items-center gap-1 rounded-md border border-cyan/30 bg-cyan/10 px-1.5 py-0.5 text-[10.5px] font-medium text-cyan">
                <Zap className="size-3" /> LIVE ANALYSIS
              </span>
            )}
          </div>
          <h1 className="mt-3 text-[28px] font-semibold leading-tight tracking-tight text-ink-1 sm:text-[34px]">{titleCase(i.name)}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12.5px] text-ink-3">
            <span className="inline-flex items-center gap-1.5"><Building2 className="size-3.5" />{i.sector}</span>
            <span>·</span>
            <span>{titleCase(i.sic_description || "")}</span>
            <span>·</span>
            <span className="num">Reports in {i.currency}</span>
            <span>·</span>
            <span className="num">CIK {i.cik}</span>
            {annual && (
              <>
                <span>·</span>
                <a href={annual.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-ink-2 hover:text-amber">
                  {annual.form} filed {fmtDate(annual.filed)} <ArrowUpRight className="size-3" />
                </a>
              </>
            )}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 lg:shrink-0 lg:flex-nowrap">
          <div className="rounded-xl border border-hairline-strong bg-panel-2/80 px-4 py-3">
            <div className="label-caps">Indicative financial risk</div>
            <div className="mt-1.5 flex items-center gap-2">
              <TierChip tier={rp.overall} className="text-[12px]" />
              <span className="num text-[11px] text-ink-3">{doc.primary}</span>
            </div>
          </div>
          <button
            onClick={onAsk}
            className="group inline-flex h-[62px] items-center gap-3 rounded-xl border border-amber/40 bg-amber/10 px-4 text-left transition-colors hover:bg-amber/15"
          >
            <MessageSquareText className="size-5 text-amber" />
            <span>
              <span className="block text-[13.5px] font-medium text-ink-1">Ask Tickmark</span>
              <span className="block text-[11.5px] text-ink-3">Cited answers · numbers verified</span>
            </span>
          </button>
        </div>
      </div>
      {doc.warnings.length > 0 && doc.risk_profile.overall === null && (
        <div className="relative flex items-start gap-2 border-t border-hairline bg-warning/5 px-5 py-2.5 text-[12px] text-warning sm:px-7">
          <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
          <span>Indicative risk band: {rp.basis}.</span>
        </div>
      )}
    </motion.section>
  );
}

function LoadingState({ ticker, live }: { ticker: string; live: boolean }) {
  const steps = live
    ? ["Resolving CIK from SEC ticker index", "Fetching submissions & XBRL companyfacts", "Normalising fiscal periods", "Computing credit metrics & risk profile"]
    : ["Loading issuer dataset"];
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!live) return;
    const id = setInterval(() => setN((x) => Math.min(x + 1, steps.length - 1)), 2200);
    return () => clearInterval(id);
  }, [live, steps.length]);
  return (
    <div className="mx-auto flex w-full max-w-[1480px] flex-col px-4 pt-10 sm:px-6">
      <div className="panel relative overflow-hidden p-8">
        <div className="flex items-center gap-3">
          <Loader2 className="size-5 animate-spin text-amber" />
          <span className="num text-lg text-ink-1">{ticker}</span>
          {live && <span className="rounded border border-cyan/30 px-1.5 py-0.5 text-[10.5px] text-cyan">LIVE</span>}
        </div>
        {live && (
          <ul className="mt-6 space-y-2">
            {steps.map((s, k) => (
              <li key={s} className={k <= n ? "text-[13px] text-ink-2" : "text-[13px] text-ink-3/50"}>
                <span className="num mr-2 text-amber">{k < n ? "✓" : k === n ? "›" : "·"}</span>
                {s}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-6 text-[12px] text-ink-3">
          {live ? "This issuer is outside the pre-computed universe, so it is analysed live from SEC EDGAR. The step list reflects the pipeline order; timing is indicative." : ""}
        </p>
      </div>
    </div>
  );
}

function LoadError({ ticker, error }: { ticker: string; error: Error & { status?: number } }) {
  return (
    <div className="mx-auto w-full max-w-[900px] px-4 pt-16 sm:px-6">
      <div className="panel p-8">
        <div className="label-caps">Analysis unavailable</div>
        <h1 className="mt-2 text-2xl font-semibold text-ink-1">{ticker}</h1>
        <p className="mt-3 text-[14px] leading-relaxed text-ink-2">{error.message}</p>
        <p className="mt-2 text-[13px] text-ink-3">
          Tickmark covers non-financial corporates that file XBRL financial statements with the SEC. Banks, insurers,
          funds and REITs need a different methodology and are excluded on purpose.
        </p>
        <Link href="/screener" className="mt-6 inline-flex items-center gap-1 text-[13px] text-amber hover:underline">
          Browse covered issuers <ArrowUpRight className="size-3.5" />
        </Link>
      </div>
    </div>
  );
}

export { titleCase } from "@/lib/format";
