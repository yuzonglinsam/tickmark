import type { Metadata } from "next";
import Link from "next/link";
import { Check, Minus, Sigma } from "lucide-react";
import { TierChip } from "@/components/common/tier-chip";
import { getUniverse } from "@/lib/server-data";

export const metadata: Metadata = { title: "Methodology" };

const FORMULAS: [string, string, string][] = [
  ["EBITDA (proxy)", "Operating income + depreciation & amortisation", "Cash-flow-statement D&A; if only depreciation is tagged, EBITDA is understated (leverage conservatively overstated). Not issuer-adjusted EBITDA."],
  ["EBIT fallback", "Pre-tax income + interest expense", "Only when no operating-income tag exists; labelled where used."],
  ["Free cash flow", "Operating cash flow − capital expenditure", "Credit FCF; not FCFF."],
  ["Debt", "Long-term borrowings incl. current maturities + short-term borrowings / commercial paper", "Leases are never added on top; finance leases count only where the issuer's own debt line already includes them. Components must come from one filing; untagged components are listed, never zero-filled."],
  ["Net debt", "Debt − cash − short-term investments (floored at zero for the risk profile)", "Simplified surplus-cash netting without haircuts."],
  ["Debt / EBITDA", "Debt ÷ EBITDA", "Annual or TTM only; quarters are never annualised. Non-positive EBITDA ⇒ not meaningful."],
  ["EBITDA / interest", "EBITDA ÷ gross interest expense", "Zero interest with debt outstanding is unresolved, not infinite cover."],
  ["CFO / debt", "Operating cash flow ÷ debt", "Proxy for S&P's FFO/debt (FFO is not an XBRL concept)."],
  ["Shareholder returns / FCF", "(Dividends + buybacks) ÷ FCF", "Above 100% means distributions are funded from the balance sheet or new debt."],
  ["Altman Z″", "6.56·WC/TA + 3.26·RE/TA + 6.72·EBIT/TA + 1.05·BE/TL", "1995 non-manufacturing version; screening only."],
];

const BANDS: [number, string, string][] = [
  [0, "< 1.5x", "> 60%"], [1, "1.5x – 2x", "45% – 60%"], [2, "2x – 3x", "30% – 45%"],
  [3, "3x – 4x", "20% – 30%"], [4, "4x – 5x", "12% – 20%"], [5, "> 5x", "< 12%"],
];

export default function Methodology() {
  const u = getUniverse();
  return (
    <div className="mx-auto max-w-[920px] px-5 pb-24 pt-10">
      <div className="label-caps">Methodology</div>
      <h1 className="mt-3 text-[34px] font-semibold leading-tight tracking-tight text-ink-1">How Tickmark computes — and where it stops.</h1>
      <p className="mt-4 text-[15.5px] leading-relaxed text-ink-2">
        Tickmark is built on one rule borrowed from audit: a number is only shown if it can be agreed to its source.
        The deterministic engine does all arithmetic; the language model writes explanations around figures it is not
        allowed to produce. This page documents every formula and limitation.
      </p>

      <Section n="01" title="Data">
        <p>
          Financial statements come from SEC EDGAR&apos;s XBRL <Code>companyfacts</Code> and <Code>submissions</Code> APIs; narrative
          evidence comes from the latest 10-K / 20-F / 40-F document. Requests declare a User-Agent and stay below SEC&apos;s
          ten-requests-per-second limit. The pre-computed universe ({u.count} issuers) is the largest NYSE/Nasdaq non-financial
          filers by the SEC index&apos;s market-value ordering, plus China-based issuers that also list in Hong Kong. Anything else
          can be analysed live from the search box.
        </p>
        <ul>
          <li>Each fact is matched to an <b>exact fiscal context</b> (start, end, form). When a later filing restates a value, the latest filed value is used and earlier values are kept as lineage.</li>
          <li>Quarterly figures are differenced from year-to-date values; TTM = latest FY + current YTD − prior comparable YTD, only when every input uses the same concept.</li>
          <li>Values stay in the reporting currency (e.g. CNY for Alibaba). No FX conversion is applied to any ratio; approximate FX is used only to size chart tiles.</li>
          <li>Banks, insurers, funds and REITs (SIC 6000–6799) are excluded: corporate leverage ratios mislead for them.</li>
        </ul>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <Legend icon={<Check className="size-3" strokeWidth={3} />} cls="border-amber/40 bg-amber/10 text-amber" t="Reported" d="Value exactly as tagged in the filing." />
          <Legend icon={<Sigma className="size-3" strokeWidth={3} />} cls="border-cyan/40 bg-cyan/10 text-cyan" t="Derived" d="Recomputed from tagged facts; every input is listed." />
          <Legend icon={<Minus className="size-3" />} cls="border-hairline-strong text-ink-3" t="Not available" d="Shown as N/A with the reason; never treated as zero." />
        </div>
      </Section>

      <Section n="02" title="Formulas">
        <div className="overflow-x-auto rounded-xl border border-hairline">
          <table className="w-full min-w-[640px] text-[13px]">
            <thead><tr className="border-b border-hairline bg-panel"><th className="label-caps px-4 py-2.5 text-left font-normal">Measure</th><th className="label-caps px-4 py-2.5 text-left font-normal">Definition</th><th className="label-caps px-4 py-2.5 text-left font-normal">Notes</th></tr></thead>
            <tbody>
              {FORMULAS.map(([a, b, c]) => (
                <tr key={a} className="border-b border-hairline/60 align-top last:border-0">
                  <td className="px-4 py-3 font-medium text-ink-1">{a}</td>
                  <td className="num px-4 py-3 text-[12px] text-ink-1">{b}</td>
                  <td className="px-4 py-3 text-[12.5px] text-ink-3">{c}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section n="03" title="Indicative financial-risk profile">
        <p>
          S&amp;P Global Ratings publishes the ratio ranges it uses to assess a corporate&apos;s <em>financial</em> risk profile
          (Corporate Methodology, standard-volatility table). Tickmark uses a simplified mapping of net leverage and CFO (a proxy, not FFO) onto those ranges on a net-debt
          basis and takes the weaker band. Business risk, industry risk, liquidity assessments and analytical adjustments are
          out of scope, so the output is <b>not a credit rating</b> and should not be read as one.
        </p>
        <div className="mt-5 overflow-hidden rounded-xl border border-hairline">
          <table className="w-full text-[13px]">
            <thead><tr className="border-b border-hairline bg-panel"><th className="label-caps px-4 py-2.5 text-left font-normal">Band</th><th className="label-caps px-4 py-2.5 text-right font-normal">Net debt / EBITDA</th><th className="label-caps px-4 py-2.5 text-right font-normal">CFO / net debt</th></tr></thead>
            <tbody>
              {BANDS.map(([t, l, c]) => (
                <tr key={t} className="border-b border-hairline/60 last:border-0"><td className="px-4 py-2.5"><TierChip tier={t} /></td><td className="num px-4 py-2.5 text-right text-ink-1">{l}</td><td className="num px-4 py-2.5 text-right text-ink-1">{c}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <h3>Headroom</h3>
        <p>With current ratio <Code>L</Code> and the next weaker band&apos;s threshold <Code>T</Code>:</p>
        <ul>
          <li>EBITDA decline before the band changes = <Code>1 − L / T</Code></li>
          <li>Additional net debt capacity = <Code>T / L − 1</Code></li>
          <li>CFO decline before CFO/debt falls below floor <Code>F</Code> = <Code>1 − F / R</Code></li>
        </ul>
        <p>Negative EBITDA or negative operating cash flow makes the ratio profile not meaningful; Tickmark says so instead of forcing a band.</p>
      </Section>

      <Section n="04" title="Scenario lab">
        <p>
          A static sensitivity, run in the browser with the same rules as the Python engine: each shock is a fraction of the
          absolute base value (so a loss deepens instead of flipping sign), cash and short-term investments are held constant,
          and nothing is forecast. It answers &ldquo;what would have to happen to move the band?&rdquo;, not &ldquo;what will happen&rdquo;.
        </p>
      </Section>

      <Section n="05" title="AI guardrails">
        <ul>
          <li><b>Memo.</b> DeepSeek receives the computed metrics, analyst context (trend, sector medians, band, headroom, maturities) and three bounded excerpts from the annual report (MD&amp;A, risk factors, debt note). It must return strict JSON: four sections × two claims, each citing known evidence IDs. Any digit in the prose fails validation, as does a memo citing fewer than two filing passages. On failure the model gets one chance to regenerate with the validator&apos;s error message; drafts that still fail are discarded — never edited into shape.</li>
          <li><b>Traditional Chinese.</b> The validated English claims are translated with the same structure and citations; the translation must also be digit-free.</li>
          <li><b>Ask Tickmark.</b> Answers are grounded in the issuer&apos;s dataset. Every number in the reply is parsed (bn / m / % / x) and matched against the SEC-derived values; matches are underlined and unmatched figures are flagged in red.</li>
          <li>A valid citation proves the evidence exists — not that it fully supports a sentence. All AI text is labelled as a draft.</li>
        </ul>
      </Section>

      <Section n="06" title="Known limitations">
        <ul>
          <li>Companyfacts only contains standard taxonomy facts; issuers that tag debt with company-specific extensions show partial or missing debt (labelled as such). Separately tagged lease liabilities are not added because XBRL does not reliably state whether they already sit inside a debt line.</li>
          <li>EBITDA is unadjusted: no add-backs for restructuring, impairments or stock-based compensation.</li>
          <li>No market data (bond spreads, CDS, equity prices) — this is a fundamental view.</li>
          <li>The sector mapping is SIC-based and approximate.</li>
          <li>Live analysis depends on SEC availability and serverless time limits.</li>
        </ul>
      </Section>

      <Section n="07" title="Built with">
        <p>
          Python (engine, tests), Flask (API), Next.js + TypeScript, Tailwind CSS, Radix UI primitives via shadcn/ui, cmdk,
          Apache ECharts, Framer Motion, DeepSeek V4 Flash. Source data: SEC EDGAR (public domain). Open-source components keep
          their own licences; see the repository&apos;s THIRD_PARTY notice.
        </p>
        <p className="mt-4"><Link href="/terminal" className="text-amber hover:underline">Open the terminal →</Link></p>
      </Section>
    </div>
  );
}

function Section({ n, title, children }: { n: string; title: string; children: React.ReactNode }) {
  return (
    <section className="mt-14 border-t border-hairline pt-8">
      <div className="flex items-baseline gap-3">
        <span className="num text-[12px] text-amber">{n}</span>
        <h2 className="text-[22px] font-semibold tracking-tight text-ink-1">{title}</h2>
      </div>
      <div className="mt-4 space-y-3 text-[14.5px] leading-relaxed text-ink-2 [&_h3]:mt-6 [&_h3]:text-[15px] [&_h3]:font-semibold [&_h3]:text-ink-1 [&_li]:pl-1 [&_ul]:list-disc [&_ul]:space-y-2 [&_ul]:pl-5 [&_b]:text-ink-1">
        {children}
      </div>
    </section>
  );
}

function Code({ children }: { children: React.ReactNode }) {
  return <code className="num rounded bg-panel-3 px-1.5 py-0.5 text-[12.5px] text-ink-1">{children}</code>;
}

function Legend({ icon, cls, t, d }: { icon: React.ReactNode; cls: string; t: string; d: string }) {
  return (
    <div className="rounded-xl border border-hairline bg-panel p-4">
      <div className="flex items-center gap-2"><span className={`inline-flex size-4 items-center justify-center rounded border ${cls}`}>{icon}</span><span className="text-[13.5px] font-medium text-ink-1">{t}</span></div>
      <p className="mt-2 text-[12.5px] text-ink-3">{d}</p>
    </div>
  );
}
