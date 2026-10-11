"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import {
  ArrowRight, ArrowUpRight, Binary, Bot, Braces, Check, Database, FileSearch, Gauge, Languages, Layers,
  LineChart, Mail, MessagesSquare, ShieldCheck, Sigma, Sparkles, Timer,
} from "lucide-react";
import { Logo, LogoMark } from "@/components/brand/logo";
import { GithubIcon } from "@/components/brand/github";
import { TierChip } from "@/components/common/tier-chip";
import { Sparkline } from "@/components/common/sparkline";
import { openCommandMenu, CommandMenu } from "@/components/shell/command-menu";
import { REPO_URL } from "@/components/shell/top-nav";
import { C } from "@/components/charts/echart";

export type LandingStats = {
  issuers: number; memos: number; facts: number; hk: number; sectors: number; asOf: string;
  tape: { t: string; tier: number | null }[];
};

const LINKEDIN = process.env.NEXT_PUBLIC_LINKEDIN_URL;

const fade = { initial: { opacity: 0, y: 14 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, margin: "-60px" }, transition: { duration: 0.5 } };

export function Landing({ s }: { s: LandingStats }) {
  return (
    <div className="relative overflow-x-clip">
      <header className="sticky top-0 z-40 border-b border-hairline/60 bg-background/70 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-[1200px] items-center gap-6 px-5">
          <Logo />
          <nav className="hidden items-center gap-5 text-[13px] text-ink-2 md:flex">
            <a href="#how" className="hover:text-ink-1">How it works</a>
            <a href="#features" className="hover:text-ink-1">Features</a>
            <Link href="/methodology" className="hover:text-ink-1">Methodology</Link>
            <a href="#about" className="hover:text-ink-1">About</a>
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <a href={REPO_URL} target="_blank" rel="noreferrer" className="text-ink-3 hover:text-ink-1" aria-label="GitHub"><GithubIcon className="size-[18px]" /></a>
            <Link href="/terminal" className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-amber px-3.5 text-[13px] font-medium text-primary-foreground transition-transform hover:-translate-y-px">
              Open terminal <ArrowRight className="size-3.5" />
            </Link>
          </div>
        </div>
        <CommandMenu />
      </header>

      {/* HERO */}
      <section className="relative">
        <div className="grid-bg pointer-events-none absolute inset-0 [mask-image:radial-gradient(60%_55%_at_50%_0%,black,transparent)]" />
        <div className="pointer-events-none absolute left-1/2 top-[-260px] h-[620px] w-[1100px] -translate-x-1/2 rounded-full bg-[radial-gradient(closest-side,rgba(242,163,58,0.18),transparent)]" />
        <div className="relative mx-auto max-w-[1200px] px-5 pb-10 pt-16 text-center sm:pt-24">
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
            className="mx-auto inline-flex items-center gap-2 rounded-full border border-hairline-strong bg-panel/80 px-3 py-1 text-[12px] text-ink-2">
            <span className="size-1.5 rounded-full bg-good shadow-[0_0_8px_var(--good)]" />
            {s.issuers} issuers · SEC XBRL as of {s.asOf} · AI memos in English &amp; 繁體中文
          </motion.div>
          <motion.h1 initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.05 }}
            className="mx-auto mt-6 max-w-[900px] text-[42px] font-semibold leading-[1.04] tracking-[-0.035em] text-ink-1 sm:text-[64px]">
            The AI credit analyst <br className="hidden sm:block" />that <span className="relative whitespace-nowrap text-amber">shows its work<TickUnderline /></span>.
          </motion.h1>
          <motion.p initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.12 }}
            className="mx-auto mt-6 max-w-[680px] text-[16px] leading-relaxed text-ink-2 sm:text-[17.5px]">
            Tickmark turns SEC filings into corporate credit research — leverage, rating-threshold headroom, debt maturity
            walls and a cited AI memo. Numbers come from code, the AI only explains, and <span className="text-ink-1">every figure ticks back to its filing</span>.
          </motion.p>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.18 }}
            className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/terminal" className="inline-flex h-11 items-center gap-2 rounded-xl bg-amber px-5 text-[14px] font-medium text-primary-foreground shadow-[0_8px_30px_rgba(242,163,58,0.25)] transition-transform hover:-translate-y-0.5">
              Open the terminal <ArrowRight className="size-4" />
            </Link>
            <Link href="/i/KO" className="inline-flex h-11 items-center gap-2 rounded-xl border border-hairline-strong bg-panel px-5 text-[14px] text-ink-1 transition-colors hover:border-amber/40">
              See Coca-Cola <span className="num text-ink-3">KO</span>
            </Link>
            <button onClick={openCommandMenu} className="inline-flex h-11 items-center gap-2 rounded-xl px-3 text-[13px] text-ink-3 hover:text-ink-1">
              or search any SEC filer <kbd className="num rounded border border-hairline-strong px-1.5 py-0.5 text-[10px]">⌘K</kbd>
            </button>
          </motion.div>
        </div>

        <motion.div initial={{ opacity: 0, y: 40, rotateX: 12 }} animate={{ opacity: 1, y: 0, rotateX: 0 }} transition={{ duration: 0.9, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
          style={{ perspective: 1600 }} className="relative mx-auto max-w-[1180px] px-5">
          <div className="relative overflow-hidden rounded-2xl border border-hairline-strong bg-panel shadow-[0_40px_120px_-20px_rgba(0,0,0,0.8),0_0_0_1px_rgba(242,163,58,0.06)]">
            <div className="flex h-9 items-center gap-2 border-b border-hairline bg-panel-2 px-4">
              <span className="size-2.5 rounded-full bg-[#3a4553]" /><span className="size-2.5 rounded-full bg-[#3a4553]" /><span className="size-2.5 rounded-full bg-[#3a4553]" />
              <span className="num ml-3 rounded-md bg-background/60 px-3 py-0.5 text-[11px] text-ink-3">tickmark · /i/KO</span>
            </div>
            <Image src="/landing/hero.png" alt="Tickmark issuer tear sheet for Coca-Cola" width={1440} height={900} priority className="h-auto w-full" />
          </div>
          <FloatingTrace />
          <FloatingAnswer />
        </motion.div>
      </section>

      {/* TAPE */}
      <section className="mt-16 border-y border-hairline bg-panel/40 py-4">
        <div className="overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_10%,black_90%,transparent)]">
          <div className="marquee flex w-max gap-6">
            {[...s.tape, ...s.tape].map((x, i) => (
              <Link key={i} href={`/i/${x.t}`} className="flex items-center gap-2">
                <span className="num text-[13px] font-semibold text-ink-2">{x.t}</span>
                <TierChip tier={x.tier} compact />
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* PRINCIPLES */}
      <section id="how" className="mx-auto max-w-[1200px] px-5 pt-24">
        <motion.div {...fade} className="max-w-2xl">
          <div className="label-caps">Why it exists</div>
          <h2 className="mt-3 text-[32px] font-semibold leading-tight tracking-tight text-ink-1 sm:text-[40px]">
            Banks won&apos;t trust an AI that can&apos;t cite its numbers. So Tickmark never lets it make them up.
          </h2>
        </motion.div>
        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {[
            { icon: Sigma, title: "Numbers come from code", body: "A Python engine reads SEC XBRL for exact fiscal periods, rebuilds debt from tagged components and computes every ratio deterministically. Restatements keep lineage." },
            { icon: Bot, title: "AI only explains", body: "DeepSeek drafts the memo from the computed metrics and real 10-K excerpts. Its text may not contain a single digit — validation rejects it — so figures live only in the audited tables." },
            { icon: Check, title: "Every figure ticks to a source", body: "Click any number: formula, inputs, XBRL concept, accession and a link to the filing. Missing data is shown as N/A with the reason — never silently treated as zero." },
          ].map((x, i) => (
            <motion.div key={x.title} {...fade} transition={{ duration: 0.5, delay: i * 0.08 }} className="panel relative overflow-hidden p-6">
              <div className="flex size-10 items-center justify-center rounded-xl border border-amber/30 bg-amber/10 text-amber"><x.icon className="size-5" /></div>
              <h3 className="mt-5 text-[17px] font-semibold text-ink-1">{x.title}</h3>
              <p className="mt-2 text-[14px] leading-relaxed text-ink-2">{x.body}</p>
            </motion.div>
          ))}
        </div>
        <Pipeline />
      </section>

      {/* FEATURES */}
      <section id="features" className="mx-auto max-w-[1200px] px-5 pt-28">
        <motion.div {...fade} className="max-w-2xl">
          <div className="label-caps">What a credit analyst gets</div>
          <h2 className="mt-3 text-[32px] font-semibold leading-tight tracking-tight text-ink-1 sm:text-[40px]">From filing to credit view in thirty seconds.</h2>
        </motion.div>
        <div className="mt-12 grid gap-4 md:grid-cols-6">
          <Feature className="md:col-span-3" icon={Gauge} title="Rating-threshold headroom"
            body="Maps net leverage and CFO/debt onto S&P's public financial-risk table and answers the question credit committees ask first: how far can EBITDA fall before the band changes?">
            <HeadroomDemo />
          </Feature>
          <Feature className="md:col-span-3" icon={MessagesSquare} title="Ask, with verified numbers"
            body="Ask anything in English or Chinese. Every figure in the answer is matched against the SEC-derived dataset and flagged if it can't be verified.">
            <AskDemo />
          </Feature>
          <Feature className="md:col-span-2" icon={Timer} title="Scenario lab" body="Shock EBITDA, cash flow, rates or debt and watch the band move, with breakpoints and a sensitivity tornado — recomputed in the browser, no AI.">
            <div className="mt-5 flex items-center gap-2"><TierChip tier={3} /><ArrowRight className="size-4 text-ink-3" /><TierChip tier={4} /><span className="ml-1 rounded-md bg-critical/15 px-2 py-0.5 text-[11px] text-critical">▼ 1 band</span></div>
          </Feature>
          <Feature className="md:col-span-2" icon={Layers} title="Maturity wall & runway" body="Contractual principal by year against cash and retained free cash flow: when would this issuer need the bond market?">
            <div className="mt-5 flex h-16 items-end gap-1.5">{[18, 48, 29, 30, 34, 62].map((h, i) => <div key={i} className="flex-1 rounded-t bg-series-1/80" style={{ height: `${h}%` }} />)}</div>
          </Feature>
          <Feature className="md:col-span-2" icon={Languages} title="Bilingual cited memos" body="Four-section credit memo in English and Traditional Chinese for Hong Kong desks. Each claim carries clickable filing citations.">
            <div className="mt-5 flex flex-wrap gap-1.5"><Chip>P2 · Risk factors</Chip><Chip>P3 · Debt note</Chip><Chip cyan>S14 · CommercialPaper</Chip></div>
          </Feature>
          <Feature className="md:col-span-2" icon={LineChart} title="Screener for 490+ issuers" body="Leverage vs. interest cover across the universe, percentile shading, sector medians and CSV export.">
            <div className="mt-5 flex gap-4"><Sparkline values={[3, 2.8, 2.4, 2.38]} width={110} height={36} /><Sparkline values={[1, 1.6, 2.4, 3.9]} width={110} height={36} color={C.s2} /></div>
          </Feature>
          <Feature className="md:col-span-2" icon={FileSearch} title="Any SEC filer, live" body="Outside the pre-computed universe? Search any of 10,000+ tickers and the same engine runs live against SEC EDGAR." />
          <Feature className="md:col-span-2" icon={ShieldCheck} title="Honest by construction" body="Banks, insurers and REITs are excluded, not forced through the wrong model. Partial debt scopes and data gaps are labelled where they appear." />
        </div>
      </section>

      {/* STATS */}
      <section className="mx-auto max-w-[1200px] px-5 pt-24">
        <div className="panel grid grid-cols-2 gap-6 p-8 md:grid-cols-4">
          {[[s.issuers, "issuers pre-computed"], [s.facts.toLocaleString("en-US"), "SEC facts linked to filings"], [s.memos, "bilingual AI memos"], [s.hk, "HK dual-listed issuers"]].map(([v, l]) => (
            <div key={l as string}>
              <div className="num text-[34px] font-semibold tracking-tight text-ink-1">{v}</div>
              <div className="mt-1 text-[13px] text-ink-3">{l}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ABOUT */}
      <section id="about" className="mx-auto max-w-[1200px] px-5 pb-24 pt-24">
        <div className="grid gap-8 md:grid-cols-[1fr_1.3fr] md:items-center">
          <motion.div {...fade}>
            <div className="label-caps">Built by</div>
            <h2 className="mt-3 text-[32px] font-semibold tracking-tight text-ink-1">Sam Yu</h2>
            <p className="mt-1 text-[14px] text-ink-3">BBA (Accounting &amp; Data Analytics), The University of Hong Kong</p>
            <div className="mt-6 flex flex-wrap gap-2">
              <a href="mailto:samuel_yu@connect.hku.hk" className="inline-flex items-center gap-2 rounded-lg border border-hairline-strong px-3 py-2 text-[13px] text-ink-2 hover:text-ink-1"><Mail className="size-4" /> Email</a>
              <a href={REPO_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-hairline-strong px-3 py-2 text-[13px] text-ink-2 hover:text-ink-1"><GithubIcon className="size-4" /> Source code</a>
              {LINKEDIN && (
                <a href={LINKEDIN} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-hairline-strong px-3 py-2 text-[13px] text-ink-2 hover:text-ink-1"><ArrowUpRight className="size-4" /> LinkedIn</a>
              )}
            </div>
          </motion.div>
          <motion.div {...fade} className="panel relative overflow-hidden p-7">
            <LogoMark className="absolute right-6 top-6 size-8 opacity-30" />
            <p className="text-[15px] leading-relaxed text-ink-2">
              As an audit intern I learned the habit behind every workpaper: a <span className="text-amber">tick mark</span> means a number has been
              agreed to its source. Tickmark applies that habit to AI-assisted credit research. I designed the financial method,
              the data contracts and the validation rules; the engine is Python, the terminal is Next.js, and every claim the
              AI makes has to survive the same tick-and-tie an auditor would apply.
            </p>
            <div className="mt-5 flex flex-wrap gap-2 text-[11.5px]">
              {["Python", "SEC XBRL", "Next.js", "TypeScript", "ECharts", "DeepSeek V4", "Flask", "Vercel"].map((t) => (
                <span key={t} className="num rounded-md border border-hairline-strong bg-panel-2 px-2 py-1 text-ink-2">{t}</span>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      <footer className="border-t border-hairline py-8">
        <div className="mx-auto flex max-w-[1200px] flex-col gap-3 px-5 text-[12px] text-ink-3 sm:flex-row sm:items-center sm:justify-between">
          <Logo className="scale-90" />
          <span>Data: SEC EDGAR (public domain). Indicative financial-risk profiles are not credit ratings. Not investment advice.</span>
        </div>
      </footer>
    </div>
  );
}

function TickUnderline() {
  return (
    <svg viewBox="0 0 300 20" className="absolute -bottom-3 left-0 h-4 w-full" preserveAspectRatio="none" aria-hidden>
      <motion.path d="M2 12 C 70 4, 150 4, 220 10 S 290 16, 298 6" fill="none" stroke="var(--amber)" strokeWidth="3" strokeLinecap="round"
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.9, delay: 0.6, ease: "easeOut" }} />
    </svg>
  );
}

function FloatingTrace() {
  return (
    <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 1.1, duration: 0.6 }}
      className="absolute -right-2 top-[30%] hidden w-[300px] rounded-xl border border-hairline-strong bg-popover/95 p-4 shadow-2xl backdrop-blur lg:block xl:-right-10">
      <div className="label-caps">SEC fact · FY2025</div>
      <div className="mt-1 flex items-baseline justify-between">
        <span className="text-[14px] font-medium text-ink-1">Commercial paper</span>
        <span className="num text-[15px] text-ink-1">1.50bn</span>
      </div>
      <div className="mt-3 inline-flex items-center gap-1.5 rounded-md border border-amber/30 bg-amber/10 px-2 py-1 text-[11px] text-amber">
        <Check className="size-3" strokeWidth={3} /> Agreed to source
      </div>
      <div className="num mt-3 rounded-lg border border-hairline bg-panel-2 p-2.5 text-[10.5px] leading-relaxed text-ink-3">
        us-gaap:CommercialPaper<br />10-K · filed 20 Feb 2026<br />0001628280-26-010047
      </div>
    </motion.div>
  );
}

function FloatingAnswer() {
  return (
    <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 1.4, duration: 0.6 }}
      className="absolute -left-2 bottom-[12%] hidden w-[330px] rounded-xl border border-hairline-strong bg-popover/95 p-4 shadow-2xl backdrop-blur lg:block xl:-left-10">
      <div className="flex items-center gap-2 text-[12px] text-ink-3"><Sparkles className="size-3.5 text-amber" /> Ask Tickmark</div>
      <p className="mt-2 text-[12.5px] leading-relaxed text-ink-2">
        Net leverage is <u className="decoration-amber/70 underline-offset-2">2.38x</u> against a <u className="decoration-amber/70 underline-offset-2">3.0x</u> threshold, so EBITDA
        could fall about <u className="decoration-amber/70 underline-offset-2">21%</u> before the band weakens.
      </p>
      <div className="mt-2.5 inline-flex items-center gap-1.5 rounded-md border border-good/30 bg-good/10 px-2 py-1 text-[11px] text-good">
        <ShieldCheck className="size-3.5" /> 3/3 figures verified against SEC data
      </div>
    </motion.div>
  );
}

function Pipeline() {
  const steps = [
    { icon: Database, t: "SEC EDGAR", d: "XBRL companyfacts, submissions, 10-K/20-F text" },
    { icon: Braces, t: "Python engine", d: "Exact fiscal contexts, TTM, debt build-up, N/A ≠ 0" },
    { icon: Binary, t: "Credit analytics", d: "Ratios, risk bands, headroom, maturities, Altman Z″" },
    { icon: Bot, t: "DeepSeek + validators", d: "Cited memo, digit-free text, number-checked Q&A" },
    { icon: LineChart, t: "Terminal", d: "Next.js + ECharts, tick-and-tie on every figure" },
  ];
  return (
    <motion.div {...fade} className="mt-10 grid gap-3 md:grid-cols-5">
      {steps.map((s, i) => (
        <div key={s.t} className="relative rounded-xl border border-hairline bg-panel-2/70 p-4">
          <div className="flex items-center gap-2"><s.icon className="size-4 text-amber" /><span className="text-[13px] font-medium text-ink-1">{s.t}</span></div>
          <p className="mt-2 text-[12px] leading-relaxed text-ink-3">{s.d}</p>
          {i < steps.length - 1 && <ArrowRight className="absolute -right-2.5 top-1/2 z-10 hidden size-4 -translate-y-1/2 text-ink-3 md:block" />}
        </div>
      ))}
    </motion.div>
  );
}

function Feature({ icon: Icon, title, body, children, className }: { icon: React.ElementType; title: string; body: string; children?: React.ReactNode; className?: string }) {
  return (
    <motion.div {...fade} className={`panel group relative overflow-hidden p-6 transition-colors hover:border-hairline-strong ${className ?? ""}`}>
      <Icon className="size-5 text-amber" />
      <h3 className="mt-4 text-[16px] font-semibold text-ink-1">{title}</h3>
      <p className="mt-2 text-[13.5px] leading-relaxed text-ink-2">{body}</p>
      {children}
    </motion.div>
  );
}

function Chip({ children, cyan }: { children: React.ReactNode; cyan?: boolean }) {
  return <span className={`num rounded-md border px-1.5 py-0.5 text-[10.5px] ${cyan ? "border-cyan/25 bg-cyan/5 text-cyan" : "border-amber/30 bg-amber/10 text-amber"}`}>{children}</span>;
}

function HeadroomDemo() {
  return (
    <div className="mt-6 space-y-3">
      <div className="flex h-2.5 gap-[3px]">
        {C.tiers.map((c, i) => <div key={i} className="flex-1 rounded-[3px]" style={{ background: c, opacity: i === 2 ? 0.95 : 0.22 }} />)}
      </div>
      <div className="num flex justify-between text-[10px] text-ink-3"><span>Minimal</span><span>1.5x</span><span>2x</span><span>3x</span><span>4x</span><span>5x</span><span>Highly lev.</span></div>
      <p className="rounded-lg border border-hairline bg-panel-2 p-3 text-[12.5px] text-ink-2">
        EBITDA could fall <b className="num text-ink-1">21%</b> before net leverage crosses <b className="num text-ink-1">3.0x</b> into <b className="text-ink-1">Significant</b>.
      </p>
    </div>
  );
}

function AskDemo() {
  return (
    <div className="mt-6 space-y-2.5">
      <div className="ml-auto w-fit rounded-xl rounded-tr-sm bg-accent px-3 py-2 text-[12.5px] text-ink-1">派息是否由自由現金流支付？</div>
      <div className="rounded-xl rounded-tl-sm border border-hairline bg-panel-2 px-3 py-2.5 text-[12.5px] leading-relaxed text-ink-2">
        否。股息及回購合共為自由現金流的 <u className="decoration-amber/70 underline-offset-2">180%</u>，差額需由資產負債表或新增借款支付。
        <div className="mt-2 inline-flex items-center gap-1.5 rounded-md border border-good/30 bg-good/10 px-2 py-0.5 text-[10.5px] text-good"><ShieldCheck className="size-3" /> 1/1 figures verified</div>
      </div>
    </div>
  );
}
