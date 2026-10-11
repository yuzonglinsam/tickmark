"use client";

import { useMemo, useState } from "react";
import { ArrowUpRight, Search, TriangleAlert } from "lucide-react";
import { Panel } from "@/components/common/panel";
import { fmtDate } from "@/lib/format";
import { useIssuerCtx } from "./source-context";

export function SourcesTab() {
  const { doc } = useIssuerCtx();
  const [q, setQ] = useState("");
  const rows = useMemo(() => {
    const all = Object.entries(doc.sources);
    const Q = q.trim().toLowerCase();
    return Q ? all.filter(([id, s]) => (id + s.concept + s.accession + s.form).toLowerCase().includes(Q)) : all;
  }, [doc, q]);
  const filings = Array.from(new Set(Object.values(doc.sources).map((s) => s.accession)));
  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <Panel eyebrow={`${Object.keys(doc.sources).length} XBRL facts from ${filings.length} filings`} title="Source register" bodyClassName="p-0"
          action={
            <label className="flex h-8 items-center gap-2 rounded-md border border-hairline-strong bg-panel-2 px-2.5">
              <Search className="size-3.5 text-ink-3" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter concept / accession"
                className="w-44 bg-transparent text-[12px] text-ink-1 outline-none placeholder:text-ink-3" />
            </label>
          }>
          <div className="scrollbar-thin max-h-[560px] overflow-auto">
            <table className="w-full min-w-[640px] text-[12px]">
              <thead className="sticky top-0 bg-panel">
                <tr className="border-b border-hairline text-left">
                  {["Ref", "XBRL concept", "Form", "Filed", "Accession", ""].map((h) => <th key={h} className="label-caps px-4 py-2.5 font-normal">{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {rows.map(([id, s]) => (
                  <tr key={id} className="border-b border-hairline/60 hover:bg-panel-2">
                    <td className="num px-4 py-1.5 text-amber">{id}</td>
                    <td className="num max-w-[300px] truncate px-4 py-1.5 text-ink-1">{s.concept}</td>
                    <td className="px-4 py-1.5 text-ink-2">{s.form}</td>
                    <td className="num px-4 py-1.5 text-ink-3">{fmtDate(s.filed)}</td>
                    <td className="num px-4 py-1.5 text-ink-3">{s.accession}</td>
                    <td className="px-4 py-1.5"><a href={s.url} target="_blank" rel="noreferrer" className="text-ink-3 hover:text-amber"><ArrowUpRight className="size-3.5" /></a></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
        <div className="space-y-4">
          <Panel eyebrow="Pipeline" title="Versions & provenance">
            <dl className="space-y-2 text-[12.5px]">
              {Object.entries(doc.versions).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-3"><dt className="capitalize text-ink-3">{k.replace("_", " ")}</dt><dd className="num text-ink-1">{v}</dd></div>
              ))}
              <div className="flex justify-between gap-3"><dt className="text-ink-3">Dataset built</dt><dd className="num text-ink-1">{doc.generated_at.replace("T", " ").replace("+00:00", " UTC")}</dd></div>
              <div className="flex justify-between gap-3"><dt className="text-ink-3">Evidence cut-off</dt><dd className="num text-ink-1">{doc.as_of}</dd></div>
              <div className="flex justify-between gap-3"><dt className="text-ink-3">Raw dataset</dt><dd><a href={doc.live ? `/api/py/analyze?ticker=${doc.issuer.ticker}` : `/data/issuers/${doc.issuer.ticker}.json`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-amber hover:underline">JSON <ArrowUpRight className="size-3" /></a></dd></div>
              <div className="flex justify-between gap-3"><dt className="text-ink-3">SEC profile</dt><dd><a href={doc.issuer.sec_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-amber hover:underline">EDGAR <ArrowUpRight className="size-3" /></a></dd></div>
            </dl>
          </Panel>
          <Panel eyebrow="Read before relying on figures" title="Data notes">
            <ul className="space-y-2.5">
              {doc.warnings.map((w, i) => (
                <li key={i} className="flex gap-2 text-[12px] leading-relaxed text-ink-2"><TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-warning" />{w}</li>
              ))}
              {doc.coverage.missing.map((m) => (
                <li key={m.key} className="flex gap-2 text-[12px] leading-relaxed text-ink-3"><span className="num shrink-0 text-ink-2">N/A</span><span><b className="font-medium text-ink-2">{m.key.replace(/_/g, " ")}:</b> {m.reason}</span></li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>
    </div>
  );
}
