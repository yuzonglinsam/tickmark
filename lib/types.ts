export type SourceRow = { concept: string; accession: string; form: string; filed: string; url: string };

export type FactRow = {
  value: number | null;
  status: "reported" | "derived" | "missing" | "scenario";
  note: string;
  sources: string[];
  restated: number;
};

export type MetricRow = {
  value: number | null;
  unit: string;
  status: "available" | "missing" | "not_meaningful";
  formula: string;
  explanation: string;
  evidence: string[];
};

export type Period = { id: string; basis: "annual" | "ttm" | "quarter"; start: string | null; end: string };

export type ScoreFactor = { name: string; weight: number; points: number | null; explanation: string };
export type Score = {
  value: number | null;
  band: string;
  coverage: number;
  lower: number;
  upper: number;
  method: string;
  factors: ScoreFactor[];
};

export type TierInfo = { tier: number | null; value: number | null; note: string };
export type Headroom = {
  leverage: {
    ratio: number;
    tier: number;
    next_threshold: number | null;
    ebitda_decline_to_downgrade: number | null;
    debt_increase_to_downgrade: number | null;
    ebitda_increase_to_upgrade: number | null;
    upgrade_threshold: number | null;
  } | null;
  cashflow: {
    ratio: number;
    tier: number;
    next_threshold: number | null;
    cfo_decline_to_downgrade: number | null;
    cfo_increase_to_upgrade: number | null;
    upgrade_threshold: number | null;
  } | null;
};
export type RiskProfile = {
  overall: number | null;
  label: string | null;
  basis: string;
  leverage: TierInfo;
  cashflow: TierInfo;
  headroom: Headroom;
  net_debt: number | null;
  gross_debt: number | null;
  liquid_assets: number | null;
  gross: { leverage: number | null; cashflow: number | null };
  basis_note: string;
  method: string;
};

export type DebtComponent = {
  label: string;
  concept: string;
  value: number;
  accession: string;
  url: string;
  filed: string;
  form: string;
};
export type DebtScope = {
  method: string;
  block: string;
  components: DebtComponent[];
  not_tagged: string[];
  leases: Record<string, DebtComponent>;
  completeness: "full" | "partial" | "none";
  definition: string;
};

export type Maturity = { bucket: string; concept: string; value: number | null; source: (DebtComponent & { ref?: string }) | null };

export type Evidence = { passage?: string; accession?: string; concept?: string };
export type Claim = { text: string; evidence: Evidence[]; metrics: string[] };
export type MemoSections = {
  credit_strengths: Claim[];
  key_risks: Claim[];
  debt_servicing_capacity: Claim[];
  overall_credit_view: Claim[];
};
export type ConsistencyCheck = {
  section: string; index: number; text: string; status: "consistent" | "conflict" | "unreviewed";
  fact_id?: string | null; formula?: string; left?: number | null; right?: number | null; actual?: string; sources?: string[];
};
export type ConsistencyReview = { status: string; checked: number; conflicts: number; unreviewed: number; checks: ConsistencyCheck[] };
export type Memo = {
  consistency?: Partial<Record<"en" | "zh", ConsistencyReview>>;
  en: MemoSections;
  zh: MemoSections | null;
  model: string;
  prompt_version: string;
  generated_at: string;
  period: string;
  status: "draft" | "reviewed";
  usage?: { input: number | null; output: number | null };
};
export type Passage = { id: string; heading: string; text: string; url: string; accession: string };

export type Filing = { form: string; accession: string; filed: string; report_date: string; url: string } | null;

export type Issuer = {
  schema: string;
  generated_at: string;
  as_of: string;
  live?: boolean;
  versions: Record<string, string>;
  issuer: {
    ticker: string;
    cik: string;
    name: string;
    exchange: string | null;
    hk: string | null;
    sic: string;
    sic_description: string;
    sector: string;
    fiscal_year_end: string;
    currency: string;
    filer_category: string;
    state: string | null;
    country: string | null;
    website: string | null;
    sec_url: string;
    mcap_rank: number | null;
  };
  primary: string;
  periods: Period[];
  facts: Record<string, Record<string, FactRow>>;
  metrics: Record<string, Record<string, MetricRow>>;
  score: Record<string, Score>;
  extended: Record<string, Record<string, FactRow | null>>;
  risk_profile: RiskProfile;
  debt_scope: DebtScope;
  maturities: Maturity[];
  altman: { value: number | null; zone: string | null; components: Record<string, number> | null };
  warnings: string[];
  coverage: { available: string[]; missing: { key: string; reason: string }[] };
  filings: { annual: Filing; quarter: Filing };
  sources: Record<string, SourceRow>;
  formulas: Record<string, string>;
  peers?: {
    sector: string;
    count: number;
    percentile: Record<string, number>;
    median: Record<string, number>;
  };
  passages?: Passage[];
  memo?: Memo;
};

export type UniverseRow = {
  t: string; n: string; s: string; hk: string | null; cur: string; fy: string; end: string;
  rev: number | null; ebitda: number | null; debt: number | null; cash: number | null; fcf: number | null;
  lev: number | null; nlev: number | null; icov: number | null; ecov: number | null; cfod: number | null;
  fcfd: number | null; om: number | null; cr: number | null; g: number | null; srf: number | null;
  tier: number | null; z: number | null; zone: string | null; score: number | null; dc: string;
  rank: number | null; memo: boolean;
  nd: number | null; liq: number | null; rlev: number | null; rcf: number | null; hd: number | null; hc: number | null; m12: number | null;
};
export type SectorStat = { count: number } & Record<string, { median: number; p25: number; p75: number; n: number } | number>;
export type Universe = {
  generated_at: string;
  count: number;
  issuers: UniverseRow[];
  sectors: Record<string, SectorStat>;
  excluded: { ticker: string; name: string; reason: string }[];
};
