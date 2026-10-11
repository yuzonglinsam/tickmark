"use client";

import { useState } from "react";
import { BadgeCheck, Copy, FileText, Hash, Languages, Loader2, Sparkles, TriangleAlert } from "lucide-react";
import { toast } from "sonner";
import { Panel } from "@/components/common/panel";
import { resolveEvidence } from "@/lib/issuer";
import { fmtDate, METRIC_LABELS, SECTION_LABELS } from "@/lib/format";
import type { Claim, Memo, Passage } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useIssuerCtx } from "./source-context";

const ORDER = ["credit_strengths", "key_risks", "debt_servicing_capacity", "overall_credit_view"] as const;

export function MemoTab() {
  const { doc, updateDoc } = useIssuerCtx();
  const [lang, setLang] = useState<"en" | "zh">("en");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const memo = doc.memo;

  const generate = async () => {
    setBusy(true);
    setErr(null);
    try {
      const r = await fetch("/api/py/memo", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ ticker: doc.issuer.ticker }) });
      const body = await r.json();
      if (!r.ok) throw new Error(body.error || `HTTP ${r.status}`);
      updateDoc({ memo: body.memo as Memo, passages: body.passages as Passage[] });
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (!memo) {
    return (
      <Panel title="AI credit memo">
        <div className="flex flex-col items-start gap-4 py-4">
          <p className="max-w-2xl text-[13.5px] leading-relaxed text-ink-2">
            No memo has been generated for this issuer yet. Generating one sends the deterministic metrics and three
            bounded excerpts from the latest annual report (MD&amp;A, risk factors, debt note) to DeepSeek, then validates
            the JSON: every claim must cite known evidence and contain no digits.
          </p>
          <button onClick={generate} disabled={busy}
            className="inline-flex items-center gap-2 rounded-lg bg-amber px-4 py-2 text-[13px] font-medium text-primary-foreground disabled:opacity-60">
            {busy ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />} {busy ? "Generating (≈20s)…" : "Generate memo"}
          </button>
          {err && <p className="text-[12.5px] text-critical">{err}</p>}
        </div>
      </Panel>
    );
  }

  const sections = lang === "zh" && memo.zh ? memo.zh : memo.en;
  const claims = ORDER.flatMap((k) => sections[k] ?? []);
  const cited = claims.filter((c) => c.evidence.length > 0).length;
  const resolved = claims.flatMap((c) => c.evidence).filter((e) => resolveEvidence(doc, e)).length;
  const total = claims.flatMap((c) => c.evidence).length;
  const digitFree = !claims.some((c) => /[0-9]/.test(c.text));

  return (
    <div className="space-y-4">
      <div className="panel flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-md border border-warning/40 bg-warning/10 px-2 py-0.5 text-[11px] font-medium text-warning">DRAFT · AI-generated</span>
            <span className="num text-[11.5px] text-ink-3">{memo.model} · {memo.prompt_version} · {fmtDate(memo.generated_at.slice(0, 10))}</span>
          </div>
          <h2 className="mt-2 text-[18px] font-semibold text-ink-1">{lang === "zh" ? "信用研究備忘錄" : "Credit research memo"} · {doc.issuer.ticker} · {doc.primary}</h2>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Check ok label={`${cited}/${claims.length} claims cited`} />
          <Check ok={resolved === total} label={`${resolved}/${total} citations resolve to filings`} />
          <Check ok={digitFree} label="No numbers in AI text" />
          <button onClick={() => copyMarkdown(doc.issuer.name, doc.issuer.ticker, doc.primary, sections, lang, memo)}
            className="inline-flex items-center gap-1.5 rounded-md border border-hairline-strong px-2 py-1 text-[11.5px] text-ink-2 hover:text-ink-1">
            <Copy className="size-3.5" /> Copy
          </button>
          <div className="ml-1 flex rounded-lg border border-hairline-strong p-0.5">
            <LangBtn on={lang === "en"} onClick={() => setLang("en")}>EN</LangBtn>
            <LangBtn on={lang === "zh"} onClick={() => setLang("zh")} disabled={!memo.zh}><Languages className="size-3.5" />繁中</LangBtn>
          </div>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {ORDER.map((k) => (
          <Panel key={k} eyebrow={lang === "zh" ? SECTION_LABELS[k].en : undefined} title={lang === "zh" ? SECTION_LABELS[k].zh : SECTION_LABELS[k].en}>
            <div className="space-y-4">
              {(sections[k] ?? []).map((c, i) => <ClaimView key={i} c={c} lang={lang} />)}
            </div>
          </Panel>
        ))}
      </div>
      <Passages />
      <p className="flex items-start gap-2 text-[11.5px] leading-relaxed text-ink-3">
        <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
        A valid citation proves the evidence exists, not that it fully supports the sentence. Treat the memo as a first draft for
        analyst review. Figures intentionally live only in the deterministic tables.
      </p>
    </div>
  );
}

function Check({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11.5px]", ok ? "border-good/30 bg-good/10 text-good" : "border-warning/30 bg-warning/10 text-warning")}>
      <BadgeCheck className="size-3.5" /> {label}
    </span>
  );
}

function LangBtn({ on, children, onClick, disabled }: { on: boolean; children: React.ReactNode; onClick: () => void; disabled?: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled}
      className={cn("inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-[12px] disabled:opacity-40", on ? "bg-accent text-ink-1" : "text-ink-3 hover:text-ink-1")}>
      {children}
    </button>
  );
}

function ClaimView({ c, lang }: { c: Claim; lang: "en" | "zh" }) {
  const { doc, trace } = useIssuerCtx();
  return (
    <div className="group">
      <p className={cn("text-[13.5px] leading-relaxed text-ink-2", lang === "zh" && "text-[14px] leading-[1.9]")}>{c.text}</p>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {c.evidence.map((e, i) => {
          const r = resolveEvidence(doc, e);
          if (!r) return null;
          if (r.kind === "passage") {
            const p = doc.passages?.find((x) => x.id === r.id);
            return (
              <button key={i} onClick={() => trace({ kind: "passage", id: r.id })}
                className="inline-flex items-center gap-1 rounded-md border border-amber/30 bg-amber/10 px-1.5 py-0.5 text-[10.5px] text-amber hover:border-amber/60">
                <FileText className="size-3" /> {r.id} · {p?.heading ?? "Filing"}
              </button>
            );
          }
          const s = doc.sources[r.id];
          return (
            <button key={i} onClick={() => trace({ kind: "source", id: r.id })}
              className="num inline-flex items-center gap-1 rounded-md border border-cyan/25 bg-cyan/5 px-1.5 py-0.5 text-[10px] text-cyan hover:border-cyan/50">
              {r.id} · {s.concept.replace(/^.*:/, "").replace(/([a-z])([A-Z])/g, "$1 $2").slice(0, 34)}
            </button>
          );
        })}
        {c.metrics.map((m) => (
          <button key={m} onClick={() => trace({ kind: "metric", key: m, period: doc.primary })}
            className="inline-flex items-center gap-1 rounded-md border border-hairline-strong px-1.5 py-0.5 text-[10.5px] text-ink-2 hover:border-ink-3">
            <Hash className="size-3" /> {METRIC_LABELS[m] ?? m}
          </button>
        ))}
      </div>
    </div>
  );
}

function Passages() {
  const { doc, trace } = useIssuerCtx();
  if (!doc.passages?.length) return null;
  return (
    <Panel eyebrow="Evidence sent to the model" title="Filing passages">
      <div className="grid gap-3 md:grid-cols-3">
        {doc.passages.map((p) => (
          <button key={p.id} onClick={() => trace({ kind: "passage", id: p.id })}
            className="rounded-lg border border-hairline bg-panel-2 p-3.5 text-left transition-colors hover:border-amber/40">
            <div className="flex items-center gap-2 text-[12px] text-amber"><FileText className="size-3.5" /> {p.id} · {p.heading}</div>
            <p className="mt-2 line-clamp-4 text-[12px] leading-relaxed text-ink-3">{p.text}</p>
          </button>
        ))}
      </div>
    </Panel>
  );
}

function copyMarkdown(name: string, ticker: string, period: string, sections: Record<string, Claim[]>, lang: "en" | "zh", memo: Memo) {
  const lines = [`# ${name} (${ticker}) — ${lang === "zh" ? "信用研究備忘錄" : "Credit memo"} · ${period}`, "",
    `_Draft generated by ${memo.model} (${memo.prompt_version}) on ${memo.generated_at.slice(0, 10)}. Figures: see Tickmark tables._`, ""];
  for (const k of ORDER) {
    lines.push(`## ${lang === "zh" ? SECTION_LABELS[k].zh : SECTION_LABELS[k].en}`, "");
    for (const c of sections[k] ?? []) lines.push(`- ${c.text}`);
    lines.push("");
  }
  navigator.clipboard.writeText(lines.join("\n")).then(() => toast.success("Memo copied as Markdown"));
}
