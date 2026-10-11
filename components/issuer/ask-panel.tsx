"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, BadgeCheck, FileText, Loader2, ShieldAlert, Sparkles } from "lucide-react";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { resolveEvidence } from "@/lib/issuer";
import type { Evidence } from "@/lib/types";
import { cn } from "@/lib/utils";
import { LogoMark } from "@/components/brand/logo";
import { useIssuerCtx } from "./source-context";

type NumberCheck = { text: string; verified: boolean; matched?: string };
type Msg = { role: "user" | "assistant"; text: string; evidence?: Evidence[]; numbers?: NumberCheck[]; error?: boolean };

const SUGGESTED = [
  "What is the single biggest credit risk here?",
  "How much headroom is there before the risk band weakens?",
  "Are dividends and buybacks funded by free cash flow?",
  "When does the maturity wall bite, and is liquidity enough?",
  "用繁體中文總結這家公司的信用狀況",
];

export function AskPanel() {
  const { doc, askOpen, setAskOpen, pendingQuestion, consumeQuestion, trace } = useIssuerCtx();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, busy]);

  const send = async (question: string) => {
    const text = question.trim();
    if (!text || busy) return;
    setQ("");
    const history = msgs.slice(-6).map((m) => ({ role: m.role, content: m.text }));
    setMsgs((m) => [...m, { role: "user", text }]);
    setBusy(true);
    try {
      const r = await fetch("/api/py/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ ticker: doc.issuer.ticker, question: text, history, live: !!doc.live }),
      });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(body.error || `The analyst service returned HTTP ${r.status}.`);
      setMsgs((m) => [...m, { role: "assistant", text: body.answer, evidence: body.evidence, numbers: body.numbers }]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "assistant", text: (e as Error).message, error: true }]);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (askOpen && pendingQuestion) {
      send(pendingQuestion);
      consumeQuestion();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [askOpen, pendingQuestion]);

  return (
    <Sheet open={askOpen} onOpenChange={setAskOpen}>
      <SheetContent side="right" className="flex w-full flex-col gap-0 border-hairline-strong bg-popover p-0 sm:max-w-[500px]">
        <SheetHeader className="border-b border-hairline px-5 py-4">
          <SheetTitle className="flex items-center gap-2.5 text-[15px] text-ink-1">
            <LogoMark className="size-6" /> Ask Tickmark <span className="num text-[12px] font-normal text-ink-3">· {doc.issuer.ticker}</span>
          </SheetTitle>
          <SheetDescription className="text-[12px] text-ink-3">
            Answers use only this issuer&apos;s SEC-derived figures and filing excerpts. Every number in an answer is checked against the dataset.
          </SheetDescription>
        </SheetHeader>
        <div className="scrollbar-thin flex-1 space-y-4 overflow-y-auto px-5 py-5">
          {msgs.length === 0 && (
            <div className="space-y-2">
              <div className="label-caps mb-3">Try asking</div>
              {SUGGESTED.map((s) => (
                <button key={s} onClick={() => send(s)}
                  className="flex w-full items-center gap-2 rounded-lg border border-hairline bg-panel px-3 py-2.5 text-left text-[13px] text-ink-2 transition-colors hover:border-amber/40 hover:text-ink-1">
                  <Sparkles className="size-3.5 shrink-0 text-amber" /> {s}
                </button>
              ))}
            </div>
          )}
          {msgs.map((m, i) =>
            m.role === "user" ? (
              <div key={i} className="ml-10 rounded-xl rounded-tr-sm bg-accent px-3.5 py-2.5 text-[13.5px] text-ink-1">{m.text}</div>
            ) : (
              <div key={i} className={cn("rounded-xl rounded-tl-sm border px-4 py-3", m.error ? "border-critical/30 bg-critical/5" : "border-hairline bg-panel")}>
                <p className="whitespace-pre-wrap text-[13.5px] leading-relaxed text-ink-2">
                  {m.numbers?.length ? highlight(m.text, m.numbers) : m.text}
                </p>
                {!!m.numbers?.length && <Verification numbers={m.numbers} />}
                {!!m.evidence?.length && (
                  <div className="mt-2.5 flex flex-wrap gap-1.5">
                    {m.evidence.map((e, k) => {
                      const r = resolveEvidence(doc, e);
                      if (!r) return null;
                      return (
                        <button key={k} onClick={() => trace(r.kind === "passage" ? { kind: "passage", id: r.id } : { kind: "source", id: r.id })}
                          className={cn("num inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10.5px]",
                            r.kind === "passage" ? "border-amber/30 bg-amber/10 text-amber" : "border-cyan/25 bg-cyan/5 text-cyan")}>
                          {r.kind === "passage" && <FileText className="size-3" />}
                          {r.id}{r.kind === "source" ? ` · ${doc.sources[r.id]?.concept.replace(/^.*:/, "").slice(0, 26)}` : ""}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            ),
          )}
          {busy && (
            <div className="flex items-center gap-2 text-[12.5px] text-ink-3">
              <Loader2 className="size-4 animate-spin text-amber" /> Reading the filing evidence…
            </div>
          )}
          <div ref={end} />
        </div>
        <form onSubmit={(e) => { e.preventDefault(); send(q); }} className="border-t border-hairline p-3">
          <div className="flex items-end gap-2 rounded-xl border border-hairline-strong bg-panel px-3 py-2 focus-within:border-amber/50">
            <textarea value={q} onChange={(e) => setQ(e.target.value)} rows={1} placeholder="Ask about leverage, liquidity, risks… (EN / 中文)"
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(q); } }}
              className="max-h-32 min-h-[24px] flex-1 resize-none bg-transparent text-[13.5px] text-ink-1 outline-none placeholder:text-ink-3" />
            <button type="submit" disabled={!q.trim() || busy} className="flex size-8 items-center justify-center rounded-lg bg-amber text-primary-foreground disabled:opacity-40">
              <ArrowUp className="size-4" />
            </button>
          </div>
          <p className="mt-2 px-1 text-[10.5px] text-ink-3">AI can be wrong. Verified figures are underlined; anything unverified is flagged.</p>
        </form>
      </SheetContent>
    </Sheet>
  );
}

function Verification({ numbers }: { numbers: NumberCheck[] }) {
  const ok = numbers.filter((n) => n.verified).length;
  const all = ok === numbers.length;
  return (
    <div className={cn("mt-3 inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px]",
      all ? "border-good/30 bg-good/10 text-good" : "border-warning/30 bg-warning/10 text-warning")}>
      {all ? <BadgeCheck className="size-3.5" /> : <ShieldAlert className="size-3.5" />}
      {ok}/{numbers.length} figures verified against SEC-derived data{!all && " · red = not in dataset"}
    </div>
  );
}

function highlight(text: string, numbers: NumberCheck[]) {
  const parts: React.ReactNode[] = [];
  let rest = text;
  let key = 0;
  const sorted = [...numbers].sort((a, b) => text.indexOf(a.text) - text.indexOf(b.text));
  for (const n of sorted) {
    const i = rest.indexOf(n.text);
    if (i < 0) continue;
    parts.push(rest.slice(0, i));
    parts.push(
      <span key={key++} title={n.verified ? `Matches ${n.matched}` : "Not found in the dataset — possibly computed by the model. Verify before use."}
        className={cn("num rounded px-0.5", n.verified ? "bg-amber/10 text-ink-1 underline decoration-amber/60 underline-offset-2" : "bg-critical/10 text-critical underline decoration-wavy decoration-critical/70")}>
        {n.text}
      </span>,
    );
    rest = rest.slice(i + n.text.length);
  }
  parts.push(rest);
  return parts;
}
