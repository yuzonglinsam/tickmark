"use client";

import { createContext, useCallback, useContext, useState } from "react";
import type { Issuer } from "@/lib/types";

export type TraceTarget =
  | { kind: "fact"; key: string; period: string; label?: string }
  | { kind: "metric"; key: string; period: string; label?: string }
  | { kind: "source"; id: string }
  | { kind: "passage"; id: string }
  | { kind: "debt" };

type Ctx = {
  doc: Issuer;
  updateDoc: (patch: Partial<Issuer>) => void;
  period: string;
  setPeriod: (p: string) => void;
  trace: (t: TraceTarget) => void;
  target: TraceTarget | null;
  close: () => void;
  askOpen: boolean;
  setAskOpen: (v: boolean) => void;
  ask: (q: string) => void;
  pendingQuestion: string | null;
  consumeQuestion: () => void;
};

const IssuerCtx = createContext<Ctx | null>(null);

export function IssuerProvider({ doc: initial, children }: { doc: Issuer; children: React.ReactNode }) {
  const [doc, setDoc] = useState(initial);
  const updateDoc = useCallback((patch: Partial<Issuer>) => setDoc((d) => ({ ...d, ...patch })), []);
  const [period, setPeriod] = useState(doc.primary);
  const [target, setTarget] = useState<TraceTarget | null>(null);
  const [askOpen, setAskOpen] = useState(false);
  const [pendingQuestion, setPending] = useState<string | null>(null);
  const trace = useCallback((t: TraceTarget) => setTarget(t), []);
  const close = useCallback(() => setTarget(null), []);
  const ask = useCallback((q: string) => {
    setPending(q);
    setAskOpen(true);
  }, []);
  return (
    <IssuerCtx.Provider
      value={{ doc, updateDoc, period, setPeriod, trace, target, close, askOpen, setAskOpen, ask, pendingQuestion, consumeQuestion: () => setPending(null) }}
    >
      {children}
    </IssuerCtx.Provider>
  );
}

export function useIssuerCtx() {
  const c = useContext(IssuerCtx);
  if (!c) throw new Error("useIssuerCtx outside IssuerProvider");
  return c;
}
