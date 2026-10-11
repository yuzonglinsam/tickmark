"use client";
import { useEffect, useState } from "react";
import type { Issuer, Universe } from "./types";

const cache = new Map<string, Promise<unknown>>();

export function fetchJson<T>(url: string): Promise<T> {
  if (!cache.has(url)) {
    const p = fetch(url).then(async (r) => {
      if (!r.ok) {
        const body = await r.json().catch(() => ({}));
        throw Object.assign(new Error(body.error || `HTTP ${r.status}`), { status: r.status, body });
      }
      return r.json();
    });
    p.catch(() => cache.delete(url));
    cache.set(url, p);
  }
  return cache.get(url) as Promise<T>;
}

export type Load<T> = { data: T | null; error: (Error & { status?: number }) | null; loading: boolean };

export function useJson<T>(url: string | null): Load<T> {
  const [state, setState] = useState<{ url: string | null; data: T | null; error: (Error & { status?: number }) | null }>(
    { url: null, data: null, error: null },
  );
  useEffect(() => {
    if (!url) return;
    let alive = true;
    fetchJson<T>(url)
      .then((data) => alive && setState({ url, data, error: null }))
      .catch((error) => alive && setState({ url, data: null, error }));
    return () => {
      alive = false;
    };
  }, [url]);
  const current = state.url === url;
  return { data: current ? state.data : null, error: current ? state.error : null, loading: !!url && !current };
}

export const useUniverse = () => useJson<Universe>("/data/universe.json");

export type TickerEntry = [string, string, number]; // ticker, name, cik
export const useTickers = (enabled: boolean) => useJson<TickerEntry[]>(enabled ? "/data/tickers.json" : null);

/** Covered issuers load from the static dataset; anything else is analysed live. */
export function useIssuer(ticker: string, covered: boolean | null) {
  const staticUrl = covered ? `/data/issuers/${ticker}.json` : null;
  const liveUrl = covered === false ? `/api/py/analyze?ticker=${encodeURIComponent(ticker)}` : null;
  return useJson<Issuer>(staticUrl ?? liveUrl);
}
