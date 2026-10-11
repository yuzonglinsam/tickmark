export const TIERS = ["Minimal", "Modest", "Intermediate", "Significant", "Aggressive", "Highly leveraged"] as const;
export const TIERS_ZH = ["極低", "溫和", "中等", "顯著", "進取", "高槓桿"] as const;
export const LEVERAGE_BOUNDS = [1.5, 2.0, 3.0, 4.0, 5.0];
export const CASHFLOW_BOUNDS = [0.6, 0.45, 0.3, 0.2, 0.12];

export const tierColor = (t: number | null | undefined) =>
  t === null || t === undefined ? "var(--ink-3)" : `var(--tier-${t})`;

export function money(v: number | null | undefined, cur = "", digits = 2): string {
  if (v === null || v === undefined || !isFinite(v)) return "N/A";
  const a = Math.abs(v);
  const [d, s] = a >= 1e12 ? [1e12, "tn"] : a >= 1e9 ? [1e9, "bn"] : a >= 1e6 ? [1e6, "m"] : a >= 1e3 ? [1e3, "k"] : [1, ""];
  const n = (v / d).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  return `${cur ? cur + " " : ""}${n}${s}`;
}

export function moneyShort(v: number | null | undefined): string {
  return money(v, "", Math.abs(v ?? 0) >= 1e11 ? 0 : 1);
}

export function times(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || !isFinite(v)) return "N/A";
  if (Math.abs(v) >= 100) return `${v.toFixed(0)}x`;
  return `${v.toFixed(digits)}x`;
}

export function pct(v: number | null | undefined, digits = 1, signed = false): string {
  if (v === null || v === undefined || !isFinite(v)) return "N/A";
  const s = (v * 100).toFixed(digits);
  return `${signed && v > 0 ? "+" : ""}${s}%`;
}

export function fmtMetric(v: number | null | undefined, unit: string, cur = ""): string {
  if (unit === "x") return times(v);
  if (unit === "ratio") return pct(v);
  return money(v, cur);
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso + (iso.length === 10 ? "T00:00:00Z" : ""));
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

export function periodLabel(p: { id: string; basis: string; end: string }): string {
  if (p.basis === "ttm") return `TTM · ${fmtDate(p.end)}`;
  return `${p.id} · ${fmtDate(p.end)}`;
}

export const METRIC_LABELS: Record<string, string> = {
  revenue: "Revenue",
  operating_income: "Operating income (EBIT)",
  depreciation_amortization: "D&A",
  operating_cash_flow: "Operating cash flow",
  capex: "Capital expenditure",
  interest_expense: "Interest expense",
  debt: "Debt",
  cash: "Cash & equivalents",
  current_assets: "Current assets",
  current_liabilities: "Current liabilities",
  ebitda_proxy: "EBITDA",
  fcf: "Free cash flow",
  net_debt: "Net debt (cash only)",
  net_debt_adj: "Net debt",
  gross_leverage: "Debt / EBITDA",
  net_leverage: "Net debt / EBITDA (cash only)",
  net_leverage_adj: "Net debt / EBITDA",
  interest_coverage: "EBIT / interest",
  ebitda_coverage: "EBITDA / interest",
  current_ratio: "Current ratio",
  fcf_to_debt: "FCF / debt",
  cfo_to_debt: "CFO / debt",
  operating_margin: "Operating margin",
  debt_to_capital: "Debt / capital",
  shareholder_returns_to_fcf: "Shareholder returns / FCF",
  revenue_growth: "Revenue growth",
  net_income: "Net income",
  gross_profit: "Gross profit",
  dividends: "Dividends paid",
  buybacks: "Share buybacks",
  acquisitions: "Acquisitions",
  debt_issued: "Debt issued",
  debt_repaid: "Debt repaid",
  sbc: "Stock-based compensation",
  interest_paid: "Cash interest paid",
  total_assets: "Total assets",
  total_liabilities: "Total liabilities",
  equity: "Shareholders' equity",
  retained_earnings: "Retained earnings",
  short_term_investments: "Short-term investments",
};

export const SECTION_LABELS: Record<string, { en: string; zh: string }> = {
  credit_strengths: { en: "Credit strengths", zh: "信用優勢" },
  key_risks: { en: "Key risks", zh: "主要風險" },
  debt_servicing_capacity: { en: "Debt servicing capacity", zh: "償債能力" },
  overall_credit_view: { en: "Overall credit view", zh: "整體信用觀點" },
};

// Approximate FX to USD, used ONLY to size bubbles/tiles across currencies.
// Never used in any ratio, table or memo.
export const FX_SIZING: Record<string, number> = {
  USD: 1, CNY: 0.14, EUR: 1.1, CAD: 0.73, GBP: 1.3, JPY: 0.0067, TWD: 0.031, DKK: 0.15,
  MXN: 0.054, BRL: 0.18, RUB: 0.012, COP: 0.00025, SEK: 0.1, ARS: 0.001, HKD: 0.128, CHF: 1.15,
  INR: 0.012, KRW: 0.00072, AUD: 0.66, ZAR: 0.055, NOK: 0.095, ILS: 0.27,
};

/** Axis tick labels: compact but never misleading (1.5bn, not "2bn"). */
export function axisMoney(v: number): string {
  if (v === 0) return "0";
  const a = Math.abs(v);
  const [d, u] = a >= 1e12 ? [1e12, "tn"] : a >= 1e9 ? [1e9, "bn"] : a >= 1e6 ? [1e6, "m"] : a >= 1e3 ? [1e3, "k"] : [1, ""];
  const n = v / d;
  return `${Number.isInteger(Math.round(n * 10) / 10) ? n.toFixed(0) : n.toFixed(1)}${u}`;
}

export function titleCase(s: string) {
  if (!s) return s;
  if (s !== s.toUpperCase()) return s;
  return s
    .toLowerCase()
    .replace(/\b([a-z])/g, (m) => m.toUpperCase())
    .replace(/\b(Inc|Corp|Co|Ltd|Plc|Nv|Sa|Ag|Llc|Lp)\b/g, (m) => (m === "Plc" ? "plc" : m))
    .replace(/\b(Ibm|Usa|Us|Nv|Sa|Ag)\b/gi, (m) => m.toUpperCase());
}
