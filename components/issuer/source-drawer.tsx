"use client";

import { ArrowUpRight, Check, FileText, Minus, Sigma, TriangleAlert } from "lucide-react";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { fact, metric, METRIC_INPUTS, prevAnnual } from "@/lib/issuer";
import { fmtDate, fmtMetric, METRIC_LABELS, money } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useIssuerCtx } from "./source-context";
import type { FactRow, Issuer } from "@/lib/types";

export function SourceDrawer() {
  const ctx = useIssuerCtx();
  const { target, close, doc } = ctx;
  return (
    <Sheet open={!!target} onOpenChange={(o) => !o && close()}>
      <SheetContent side="right" className="w-full gap-0 border-hairline-strong bg-popover p-0 sm:max-w-[520px]">
        {target && (
          <div className="scrollbar-thin flex h-full flex-col overflow-y-auto">
            {target.kind === "metric" && <MetricTrace doc={doc} keyName={target.key} period={target.period} />}
            {target.kind === "fact" && <FactTrace doc={doc} keyName={target.key} period={target.period} />}
            {target.kind === "source" && <SourceTrace doc={doc} id={target.id} />}
            {target.kind === "passage" && <PassageTrace doc={doc} id={target.id} />}
            {target.kind === "debt" && <DebtTrace doc={doc} />}
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

function Header({ eyebrow, title, value, status }: { eyebrow: string; title: string; value?: string; status?: "reported" | "derived" | "missing" }) {
  return (
    <SheetHeader className="gap-3 border-b border-hairline bg-panel px-6 pt-6 pb-5">
      <div className="label-caps">{eyebrow}</div>
      <SheetTitle className="text-lg font-semibold text-ink-1">{title}</SheetTitle>
      <SheetDescription className="sr-only">Source trace for {title}</SheetDescription>
      {value !== undefined && <div className="num text-3xl font-semibold tracking-tight text-ink-1">{value}</div>}
      {status && <StatusLine status={status} />}
    </SheetHeader>
  );
}

function StatusLine({ status }: { status: "reported" | "derived" | "missing" }) {
  const map = {
    reported: { icon: Check, text: "Agreed to source — value as tagged in the SEC filing", cls: "text-amber border-amber/30 bg-amber/10" },
    derived: { icon: Sigma, text: "Recomputed from tagged SEC facts — every input listed below", cls: "text-cyan border-cyan/30 bg-cyan/10" },
    missing: { icon: Minus, text: "Not available — shown as N/A, never assumed to be zero", cls: "text-ink-2 border-hairline-strong bg-panel-3" },
  }[status];
  const Icon = map.icon;
  return (
    <div className={cn("inline-flex w-fit items-center gap-2 rounded-md border px-2.5 py-1 text-[12px]", map.cls)}>
      <Icon className="size-3.5" strokeWidth={2.5} /> {map.text}
    </div>
  );
}

function filingUrl(doc: Issuer, accession: string, fallback: string) {
  return Object.values(doc.filings).find((f) => f?.accession === accession)?.url ?? fallback;
}

function SourceCard({ doc, id }: { doc: Issuer; id: string }) {
  const s = doc.sources[id];
  if (!s) return null;
  const url = filingUrl(doc, s.accession, s.url);
  const isFiling = !url.endsWith("/");
  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="group block rounded-lg border border-hairline bg-panel-2 p-3 transition-colors hover:border-amber/40"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="num truncate text-[12.5px] text-ink-1">{s.concept.includes(":") ? s.concept : `us-gaap:${s.concept}`}</div>
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[11.5px] text-ink-3">
            <span>Form {s.form}</span>
            <span>Filed {fmtDate(s.filed)}</span>
            <span className="num">{s.accession}</span>
          </div>
        </div>
        <span className="inline-flex shrink-0 items-center gap-1 text-[11.5px] text-amber opacity-80 group-hover:opacity-100">
          {isFiling ? "Filing" : "EDGAR"} <ArrowUpRight className="size-3.5" />
        </span>
      </div>
    </a>
  );
}

function FactBlock({ doc, label, f, unit = "money" }: { doc: Issuer; label: string; f: FactRow | null; unit?: string }) {
  const cur = doc.issuer.currency;
  const st = !f || f.value === null ? "missing" : f.status === "reported" ? "reported" : "derived";
  return (
    <div className="rounded-xl border border-hairline bg-panel p-4">
      <div className="flex items-baseline justify-between gap-3">
        <div className="flex items-center gap-2 text-[13px] text-ink-2">
          <span className={cn("inline-flex size-4 items-center justify-center rounded border",
            st === "reported" ? "border-amber/40 text-amber" : st === "derived" ? "border-cyan/40 text-cyan" : "border-hairline-strong text-ink-3")}>
            {st === "reported" ? <Check className="size-2.5" strokeWidth={3} /> : st === "derived" ? <Sigma className="size-2.5" strokeWidth={3} /> : <Minus className="size-2.5" />}
          </span>
          {label}
        </div>
        <div className="num text-[15px] font-medium text-ink-1">{unit === "money" ? money(f?.value, cur) : f?.value ?? "N/A"}</div>
      </div>
      {f?.note && (f.status !== "reported" || f.value === null) && (
        <p className="mt-2 text-[12px] leading-relaxed text-ink-3">{f.note}</p>
      )}
      {f && f.restated > 0 && (
        <p className="mt-2 inline-flex items-center gap-1.5 text-[11.5px] text-warning">
          <TriangleAlert className="size-3.5" /> Restated {f.restated}× — the latest filed value is used; earlier values kept as lineage.
        </p>
      )}
      {f && f.sources.length > 0 && (
        <div className="mt-3 space-y-2">
          {f.sources.map((sid) => <SourceCard key={sid} doc={doc} id={sid} />)}
        </div>
      )}
    </div>
  );
}

function MetricTrace({ doc, keyName, period }: { doc: Issuer; keyName: string; period: string }) {
  const m = metric(doc, period, keyName);
  if (!m && fact(doc, period, keyName)) return <FactTrace doc={doc} keyName={keyName} period={period} />;
  const label = METRIC_LABELS[keyName] ?? keyName;
  const inputs = METRIC_INPUTS[keyName] ?? [keyName];
  const prior = keyName === "revenue_growth" ? prevAnnual(doc, period) : null;
  return (
    <>
      <Header eyebrow={`Metric · ${period}`} title={label} value={m ? fmtMetric(m.value, m.unit, doc.issuer.currency) : "N/A"}
        status={!m || m.value === null ? "missing" : "derived"} />
      <div className="space-y-5 px-6 py-5">
        <section>
          <div className="label-caps mb-2">Formula</div>
          <div className="num rounded-lg border border-hairline bg-panel-2 px-3 py-2.5 text-[12.5px] text-ink-1">{m?.formula ?? doc.formulas[keyName]}</div>
          {m?.explanation && <p className="mt-2 text-[12.5px] text-ink-3">{m.explanation}</p>}
        </section>
        <section className="space-y-3">
          <div className="label-caps">Inputs · traced to filings</div>
          {inputs.map((k) => (
            <FactBlock key={k} doc={doc} label={METRIC_LABELS[k] ?? k} f={fact(doc, period, k)} />
          ))}
          {prior && <FactBlock doc={doc} label={`Revenue · ${prior}`} f={fact(doc, prior, "revenue")} />}
          {keyName.includes("debt") || keyName.includes("leverage") ? <DebtNote doc={doc} /> : null}
        </section>
      </div>
    </>
  );
}

function FactTrace({ doc, keyName, period }: { doc: Issuer; keyName: string; period: string }) {
  const f = fact(doc, period, keyName);
  const label = METRIC_LABELS[keyName] ?? keyName;
  const st = !f || f.value === null ? "missing" : f.status === "reported" ? "reported" : "derived";
  return (
    <>
      <Header eyebrow={`SEC fact · ${period}`} title={label} value={money(f?.value, doc.issuer.currency)} status={st} />
      <div className="space-y-4 px-6 py-5">
        <FactBlock doc={doc} label={label} f={f} />
        {keyName === "debt" && <DebtNote doc={doc} />}
      </div>
    </>
  );
}

function DebtNote({ doc }: { doc: Issuer }) {
  const s = doc.debt_scope;
  return (
    <div className="rounded-xl border border-hairline bg-panel-2 p-4 text-[12.5px] leading-relaxed text-ink-2">
      <div className="label-caps mb-2">Debt definition</div>
      <p>{s.definition}</p>
      {s.block && <p className="mt-2 text-ink-3">Basis used: <span className="text-ink-2">{s.block}</span></p>}
      {s.not_tagged.length > 0 && (
        <p className="mt-2 text-ink-3">Not separately tagged: {s.not_tagged.join("; ")}.</p>
      )}
    </div>
  );
}

function DebtTrace({ doc }: { doc: Issuer }) {
  const s = doc.debt_scope;
  const cur = doc.issuer.currency;
  return (
    <>
      <Header eyebrow={`Debt build-up · ${doc.primary}`} title="How debt was assembled" value={money(fact(doc, doc.primary, "debt")?.value, cur)}
        status={s.completeness === "none" ? "missing" : "derived"} />
      <div className="space-y-4 px-6 py-5">
        <DebtNote doc={doc} />
        <div className="label-caps">Components</div>
        {s.components.map((c, i) => (
          <a key={i} href={filingUrl(doc, c.accession, c.url)} target="_blank" rel="noreferrer" className="block rounded-lg border border-hairline bg-panel p-3 hover:border-amber/40">
            <div className="flex justify-between gap-3 text-[13px]">
              <span className="text-ink-2">{c.label}</span>
              <span className="num text-ink-1">{money(c.value, cur)}</span>
            </div>
            <div className="num mt-1 text-[11.5px] text-ink-3">{c.concept} · {c.form} · filed {fmtDate(c.filed)}</div>
          </a>
        ))}
        {Object.keys(s.leases).length > 0 && (
          <>
            <div className="label-caps pt-2">Excluded from debt (shown for reference)</div>
            {Object.entries(s.leases).map(([k, c]) => (
              <div key={k} className="flex justify-between rounded-lg border border-dashed border-hairline-strong px-3 py-2 text-[12.5px] text-ink-3">
                <span>{k.replace(/([A-Z])/g, " $1").trim()}</span>
                <span className="num">{money(c.value, cur)}</span>
              </div>
            ))}
          </>
        )}
      </div>
    </>
  );
}

function SourceTrace({ doc, id }: { doc: Issuer; id: string }) {
  const { trace } = useIssuerCtx();
  const s = doc.sources[id];
  const periods = [...doc.periods].sort((a, b) => Number(b.id === doc.primary) - Number(a.id === doc.primary));
  const matches = periods.flatMap((p) => Object.entries({ ...doc.extended[p.id], ...doc.facts[p.id] })
    .filter((entry): entry is [string, FactRow] => !!entry[1]?.sources.includes(id))
    .map(([key, f]) => ({ key, f, period: p })));
  // A source can feed an aggregate (debt, TTM): only a single-source reported fact is its raw value.
  const reported = matches.filter(({ f }) => f.status === "reported" && f.sources.length === 1);
  const component = s && [...doc.debt_scope.components, ...Object.values(doc.debt_scope.leases)]
    .find((c) => c.accession === s.accession && c.concept.split(":").pop() === s.concept.split(":").pop());
  const primary = reported[0];
  const value = primary?.f.value ?? component?.value;
  const related = Object.entries(doc.metrics[doc.primary] ?? {}).filter(([key, m]) =>
    m.value !== null && (METRIC_INPUTS[key] ?? []).some((input) => fact(doc, doc.primary, input)?.sources.includes(id)));
  return (
    <>
      <Header eyebrow={`Source ${id}${primary ? ` · ${primary.period.id}` : component ? ` · ${doc.primary}` : ""}`}
        title={s?.concept ?? id} value={value != null ? money(value, doc.issuer.currency, 3) : undefined}
        status={value != null ? "reported" : undefined} />
      <div className="space-y-4 px-6 py-5">
        <SourceCard doc={doc} id={id} />
        {primary && <p className="num text-[12.5px] leading-relaxed text-ink-3">
          {primary.period.start ? `${fmtDate(primary.period.start)} – ` : "As of "}{fmtDate(primary.period.end)} · {doc.issuer.currency}
        </p>}
        {related.length > 0 && <section className="space-y-3">
          <div className="label-caps">Used in calculations · {doc.primary}</div>
          {related.map(([key, m]) => <button key={key} onClick={() => trace({ kind: "metric", key, period: doc.primary })}
            className="group block w-full rounded-lg border border-hairline bg-panel-2 p-3 text-left transition-colors hover:border-amber/40">
            <div className="flex items-center justify-between gap-3 text-[13px]">
              <span className="text-ink-2">{METRIC_LABELS[key] ?? key}</span>
              <span className="num text-amber">{fmtMetric(m.value, m.unit, doc.issuer.currency)} <ArrowUpRight className="inline size-3.5" /></span>
            </div>
          </button>)}
        </section>}
        {(matches.length > 0 || component) && <section className="space-y-3">
          <div className="label-caps">Financial facts · linked to this source</div>
          {component && !primary && <FactBlock doc={doc} label={`${component.label} · ${doc.primary}`}
            f={{ value: component.value, status: "reported", sources: [id], note: "", restated: 0 }} />}
          {matches.map(({ key, f, period }) => <FactBlock key={`${period.id}-${key}`} doc={doc}
            label={`${METRIC_LABELS[key] ?? key} · ${period.id}`} f={f} />)}
        </section>}
      </div>
    </>
  );
}

function PassageTrace({ doc, id }: { doc: Issuer; id: string }) {
  const p = doc.passages?.find((x) => x.id === id);
  if (!p) return <Header eyebrow="Passage" title="Passage not found" />;
  return (
    <>
      <Header eyebrow={`Filing passage ${p.id}`} title={p.heading} />
      <div className="space-y-4 px-6 py-5">
        <a href={p.url} target="_blank" rel="noreferrer"
          className="inline-flex items-center gap-2 rounded-md border border-hairline-strong px-3 py-1.5 text-[12.5px] text-amber hover:border-amber/50">
          <FileText className="size-3.5" /> Open the annual report on SEC.gov <ArrowUpRight className="size-3.5" />
        </a>
        <blockquote className="rounded-xl border-l-2 border-amber/60 bg-panel-2 px-4 py-3 text-[13px] leading-relaxed text-ink-2">
          {p.text}
          <span className="text-ink-3"> …</span>
        </blockquote>
        <p className="num text-[11px] text-ink-3">Accession {p.accession} · excerpt extracted from the section heading in the filing body</p>
      </div>
    </>
  );
}
