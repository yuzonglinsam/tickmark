import type { Evidence, FactRow, Issuer, MetricRow, Period } from "./types";
import { CASHFLOW_BOUNDS, LEVERAGE_BOUNDS } from "./format";

export const METRIC_INPUTS: Record<string, string[]> = {
  ebitda_proxy: ["operating_income", "depreciation_amortization"],
  fcf: ["operating_cash_flow", "capex"],
  net_debt: ["debt", "cash"],
  gross_leverage: ["debt", "operating_income", "depreciation_amortization"],
  net_leverage: ["debt", "cash", "operating_income", "depreciation_amortization"],
  net_debt_adj: ["debt", "cash", "short_term_investments"],
  net_leverage_adj: ["debt", "cash", "short_term_investments", "operating_income", "depreciation_amortization"],
  interest_coverage: ["operating_income", "interest_expense"],
  ebitda_coverage: ["operating_income", "depreciation_amortization", "interest_expense"],
  current_ratio: ["current_assets", "current_liabilities"],
  fcf_to_debt: ["operating_cash_flow", "capex", "debt"],
  cfo_to_debt: ["operating_cash_flow", "debt"],
  operating_margin: ["operating_income", "revenue"],
  debt_to_capital: ["debt", "equity"],
  shareholder_returns_to_fcf: ["operating_cash_flow", "capex", "dividends", "buybacks"],
  revenue_growth: ["revenue"],
};

export const annualPeriods = (d: Issuer): Period[] => d.periods.filter((p) => p.basis === "annual");

export function fact(d: Issuer, pid: string, key: string): FactRow | null {
  return d.facts[pid]?.[key] ?? (d.extended[pid]?.[key] as FactRow | undefined) ?? null;
}
export function metric(d: Issuer, pid: string, key: string): MetricRow | null {
  return d.metrics[pid]?.[key] ?? null;
}
export function mval(d: Issuer, pid: string, key: string): number | null {
  const m = metric(d, pid, key);
  if (m && m.value !== null) return m.value;
  const f = fact(d, pid, key);
  return f?.value ?? null;
}

/** Oldest → newest annual series for a metric or fact. */
export function series(d: Issuer, key: string): { id: string; end: string; value: number | null }[] {
  return annualPeriods(d)
    .slice()
    .reverse()
    .map((p) => ({ id: p.id, end: p.end, value: mval(d, p.id, key) }));
}

export function prevAnnual(d: Issuer, pid: string): string | null {
  const a = annualPeriods(d);
  const i = a.findIndex((p) => p.id === pid);
  return i >= 0 && i + 1 < a.length ? a[i + 1].id : null;
}

/** Resolve a memo/answer citation to either a passage or an SEC source row id. */
export function resolveEvidence(d: Issuer, e: Evidence): { kind: "passage"; id: string } | { kind: "source"; id: string } | null {
  if (e.passage) return { kind: "passage", id: e.passage };
  if (!e.accession || !e.concept) return null;
  const concept = e.concept.includes(":") ? e.concept : e.concept;
  for (const [id, s] of Object.entries(d.sources)) {
    if (s.accession === e.accession && (s.concept === concept || s.concept.endsWith(":" + concept) || concept.endsWith(s.concept))) {
      return { kind: "source", id };
    }
  }
  return null;
}

export function tierFromLeverage(l: number | null, debtZero = false): number | null {
  if (debtZero) return 0;
  if (l === null || !isFinite(l)) return null;
  for (let i = 0; i < LEVERAGE_BOUNDS.length; i++) if (l < LEVERAGE_BOUNDS[i]) return i;
  return 5;
}
export function tierFromCashflow(r: number | null, debtZero = false): number | null {
  if (debtZero) return 0;
  if (r === null || !isFinite(r)) return null;
  for (let i = 0; i < CASHFLOW_BOUNDS.length; i++) if (r > CASHFLOW_BOUNDS[i]) return i;
  return 5;
}

export type ScenarioInput = { ebitda: number; interest: number; cfo: number; debt: number };
export type ScenarioResult = {
  ebitda: number | null; interest: number | null; cfo: number | null; netDebt: number | null; debt: number | null;
  leverage: number | null; cashflow: number | null; coverage: number | null;
  levTier: number | null; cfTier: number | null; overall: number | null; burning: boolean;
};

/**
 * Same rules as engine/credit_workbench/stress.py + scorecard.py:
 * shocks are fractions of |base| (so a negative base deteriorates further), other
 * inputs are held constant, and the profile uses net debt (debt − cash − ST investments).
 */
export function runScenario(base: {
  ebitda: number | null; interest: number | null; cfo: number | null; debt: number | null; liquid: number | null;
}, s: ScenarioInput): ScenarioResult {
  const shock = (v: number | null, c: number) => (v === null ? null : v + Math.abs(v) * c);
  const ebitda = shock(base.ebitda, s.ebitda);
  const interest = shock(base.interest, s.interest);
  const cfo = shock(base.cfo, s.cfo);
  const debt = base.debt === null ? null : base.debt * (1 + s.debt);
  const netDebt = debt === null ? null : Math.max(0, debt - (base.liquid ?? 0));
  const debtZero = netDebt === 0;
  const leverage = netDebt === null || ebitda === null ? null : debtZero ? 0 : ebitda <= 0 ? null : netDebt / ebitda;
  const cashflow = netDebt === null || cfo === null || debtZero ? null : cfo / netDebt;
  const coverage = ebitda === null || !interest ? null : ebitda / interest;
  const levTier = netDebt === null || ebitda === null ? null : debtZero ? 0 : ebitda <= 0 ? 5 : tierFromLeverage(leverage);
  const cfTier = netDebt === null || cfo === null ? null : debtZero ? 0 : tierFromCashflow(cashflow);
  const burning = (ebitda !== null && ebitda <= 0) || (cfo !== null && cfo < 0);
  const tiers = [levTier, cfTier].filter((t): t is number => t !== null);
  const overall = burning || !tiers.length ? null : Math.max(...tiers);
  return { ebitda, interest, cfo, netDebt, debt, leverage, cashflow, coverage, levTier, cfTier, overall, burning };
}

export function scenarioBase(d: Issuer) {
  const pid = d.primary;
  return {
    ebitda: mval(d, pid, "ebitda_proxy"),
    interest: fact(d, pid, "interest_expense")?.value ?? null,
    cfo: fact(d, pid, "operating_cash_flow")?.value ?? null,
    debt: fact(d, pid, "debt")?.value ?? null,
    liquid: d.risk_profile.liquid_assets,
  };
}
