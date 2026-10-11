"""Serialize one issuer's deterministic research into the Tickmark JSON contract.

Everything numeric in the web app comes from this file's output. Each value
carries the SEC sources it was computed from (short source IDs ``S1…`` resolve
in the ``sources`` table), so the UI can "tick and tie" any figure back to the
filing.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from .debt import maturity_ladder
from .metrics import FORMULAS, calculate, revenue_growth
from .models import Fact, Period, Snapshot
from .normalize import (ANNUAL_FORMS, EXTRACTOR_VERSION, NormalizedResearch, _find, _missing,
                        debt_scope, normalize)
from .scorecard import altman_z_double_prime, risk_profile
from .scoring import METHODOLOGY_VERSION, score
from .sectors import sector

SCHEMA = "tickmark-issuer-v1"

EXTENDED_FLOWS = {
    "net_income": ("NetIncomeLoss", "ProfitLoss", "ifrs-full:ProfitLoss",
                   "ifrs-full:ProfitLossAttributableToOwnersOfParent"),
    "gross_profit": ("GrossProfit", "ifrs-full:GrossProfit"),
    "dividends": ("PaymentsOfDividends", "PaymentsOfDividendsCommonStock",
                  "ifrs-full:DividendsPaidClassifiedAsFinancingActivities"),
    "buybacks": ("PaymentsForRepurchaseOfCommonStock", "PaymentsForRepurchaseOfEquity",
                 "ifrs-full:PaymentsToAcquireOrRedeemEntitysShares"),
    "acquisitions": ("PaymentsToAcquireBusinessesNetOfCashAcquired",
                     "ifrs-full:CashFlowsUsedInObtainingControlOfSubsidiariesOrOtherBusinessesClassifiedAsInvestingActivities"),
    "debt_issued": ("ProceedsFromIssuanceOfLongTermDebt", "ProceedsFromIssuanceOfDebt",
                    "ProceedsFromIssuanceOfSeniorLongTermDebt",
                    "ifrs-full:ProceedsFromBorrowingsClassifiedAsFinancingActivities"),
    "debt_repaid": ("RepaymentsOfLongTermDebt", "RepaymentsOfDebt", "RepaymentsOfSeniorDebt",
                    "ifrs-full:RepaymentsOfBorrowingsClassifiedAsFinancingActivities"),
    "sbc": ("ShareBasedCompensation", "ifrs-full:AdjustmentsForSharebasedPayments"),
    "interest_paid": ("InterestPaidNet", "InterestPaid", "ifrs-full:InterestPaidClassifiedAsOperatingActivities",
                      "ifrs-full:InterestPaidClassifiedAsFinancingActivities"),
}
EXTENDED_STOCKS = {
    "total_assets": ("Assets", "ifrs-full:Assets"),
    "total_liabilities": ("Liabilities", "ifrs-full:Liabilities"),
    "equity": ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
               "ifrs-full:EquityAttributableToOwnersOfParent", "ifrs-full:Equity"),
    "retained_earnings": ("RetainedEarningsAccumulatedDeficit", "ifrs-full:RetainedEarnings"),
    "short_term_investments": ("ShortTermInvestments", "MarketableSecuritiesCurrent",
                               "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
                               "ifrs-full:CurrentInvestments"),
}
EXTRA_FORMULAS = {
    "ebitda_coverage": "EBITDA proxy / gross interest expense",
    "cfo_to_debt": "Operating cash flow (annual or TTM) / debt (FFO/Debt proxy)",
    "debt_to_capital": "Debt / (debt + shareholders' equity)",
    "shareholder_returns_to_fcf": "(Dividends + buybacks) / free cash flow",
    "revenue_growth": "Revenue / prior comparable fiscal year revenue - 1",
    "net_debt_adj": "Debt - cash - short-term investments",
    "net_leverage_adj": "(Debt - cash - short-term investments) / EBITDA proxy (annual or TTM)",
}


class SourceTable:
    def __init__(self):
        self.ids: dict[str, str] = {}
        self.rows: dict[str, dict] = {}

    def ref(self, source) -> str:
        if source.evidence_id not in self.ids:
            short = f"S{len(self.ids) + 1}"
            self.ids[source.evidence_id] = short
            self.rows[short] = {"concept": source.concept, "accession": source.accession,
                                "form": source.form, "filed": source.filed_on.isoformat(),
                                "url": source.url}
        return self.ids[source.evidence_id]


def _fact(fact: Fact, table: SourceTable) -> dict:
    return {"value": fact.value, "status": fact.status, "note": fact.note,
            "sources": [table.ref(s) for s in fact.sources],
            "restated": len(fact.lineage)}


def _period_id(p: Period) -> str:
    if p.basis == "annual":
        return f"FY{p.end.year}"
    if p.basis == "ttm":
        return f"TTM {p.end.isoformat()}"
    return f"Q {p.end.isoformat()}"


def _ratio(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def _extended(companyfacts, research: NormalizedResearch, snap: Snapshot, table: SourceTable) -> dict:
    out = {}
    instant = Period(None, snap.flow_period.end, "instant")
    for key, concepts in EXTENDED_FLOWS.items():
        f = _find(companyfacts, research.cik, concepts, snap.currency, snap.flow_period, snap.as_of, ANNUAL_FORMS)
        out[key] = _fact(f, table) if f else None
    for key, concepts in EXTENDED_STOCKS.items():
        f = _find(companyfacts, research.cik, concepts, snap.currency, instant, snap.as_of, ANNUAL_FORMS)
        out[key] = _fact(f, table) if f else None
    return out


def _metric_rows(snap: Snapshot, table: SourceTable, ext: dict | None, prior: Snapshot | None) -> dict:
    metrics = calculate(snap)
    ids = {}
    for f in snap.facts.values():
        for s in f.sources:
            ids[s.evidence_id] = table.ref(s)
    rows = {name: {"value": m.value, "unit": m.unit, "status": m.status, "formula": m.formula,
                   "explanation": m.explanation, "evidence": [ids[e] for e in m.evidence_ids if e in ids]}
            for name, m in metrics.items()}
    v = lambda k: snap.facts[k].value if k in snap.facts else None  # noqa: E731
    annual = snap.flow_period.basis in {"annual", "ttm"}
    ebitda = metrics["ebitda_proxy"].value
    debt = v("debt")

    def extra(name, value, unit, keys, explanation=""):
        ev = sorted({table.ref(s) for k in keys if k in snap.facts for s in snap.facts[k].sources})
        status = "available" if value is not None else "missing"
        rows[name] = {"value": value, "unit": unit, "status": status, "formula": EXTRA_FORMULAS[name],
                      "explanation": explanation if value is None else "", "evidence": ev}

    interest = v("interest_expense")
    extra("ebitda_coverage", ebitda / interest if ebitda is not None and interest else None, "x",
          ("operating_income", "depreciation_amortization", "interest_expense"),
          "Requires EBITDA proxy and positive interest expense")
    extra("cfo_to_debt", _ratio(v("operating_cash_flow"), debt) if annual and debt else None, "ratio",
          ("operating_cash_flow", "debt"), "Requires annual/TTM CFO and positive debt")
    equity = ext.get("equity", {}) if ext else {}
    eq_val = equity.get("value") if equity else None
    extra("debt_to_capital", _ratio(debt, debt + eq_val) if debt is not None and eq_val is not None
          and debt + eq_val > 0 else None, "ratio", ("debt",), "Requires debt and positive capital")
    if ext:
        div = (ext.get("dividends") or {}).get("value") or 0
        bb = (ext.get("buybacks") or {}).get("value") or 0
        fcf = metrics["fcf"].value
        val = (div + bb) / fcf if fcf and fcf > 0 and (ext.get("dividends") or ext.get("buybacks")) else None
        extra("shareholder_returns_to_fcf", val, "ratio", ("operating_cash_flow", "capex"),
              "Requires positive FCF and a dividend or buyback tag")
    sti = ((ext or {}).get("short_term_investments") or {}).get("value")
    cash = v("cash")
    nd = None if debt is None or cash is None else debt - cash - (sti or 0)
    sti_refs = list(((ext or {}).get("short_term_investments") or {}).get("sources", []))
    extra("net_debt_adj", nd, snap.currency, ("debt", "cash"), "Requires debt and cash")
    rows["net_debt_adj"]["evidence"] = sorted(set(rows["net_debt_adj"]["evidence"]) | set(sti_refs))
    nla = nd / ebitda if nd is not None and ebitda and ebitda > 0 and annual else None
    extra("net_leverage_adj", nla, "x", ("debt", "cash", "operating_income", "depreciation_amortization"),
          "Requires annual/TTM EBITDA > 0, debt and cash")
    rows["net_leverage_adj"]["evidence"] = sorted(set(rows["net_leverage_adj"]["evidence"]) | set(sti_refs))
    growth = revenue_growth(snap, prior) if prior else None
    extra("revenue_growth", growth.value if growth else None, "ratio", ("revenue",),
          "Requires a comparable prior fiscal year")
    return rows


def _score(snap: Snapshot) -> dict:
    s = score(snap)
    return {"value": s.value, "band": s.band, "coverage": s.coverage, "lower": s.lower_bound,
            "upper": s.upper_bound, "method": s.methodology,
            "factors": [{"name": f.name, "weight": f.weight, "points": f.points, "explanation": f.explanation}
                        for f in s.factors]}


def latest_filing(submissions: dict, forms: set[str]) -> dict | None:
    recent = submissions.get("filings", {}).get("recent", {})
    for i, form in enumerate(recent.get("form", [])):
        if form in forms:
            acc = recent["accessionNumber"][i]
            cik = int(submissions["cik"])
            return {"form": form, "accession": acc, "filed": recent["filingDate"][i],
                    "report_date": recent["reportDate"][i],
                    "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/"
                           f"{recent['primaryDocument'][i]}"}
    return None


def build_issuer(meta: dict, submissions: dict, companyfacts: dict, as_of: date | None = None) -> dict:
    as_of = as_of or date.today()
    ticker = meta["ticker"]
    research = normalize(submissions, companyfacts, ticker, as_of)
    table = SourceTable()
    snaps: list[Snapshot] = list(research.annual)
    if research.ttm:
        snaps.append(research.ttm)
    periods, facts, metrics, scores, extended = [], {}, {}, {}, {}
    annual = list(research.annual)
    for snap in snaps:
        pid = _period_id(snap.flow_period)
        periods.append({"id": pid, "basis": snap.flow_period.basis,
                        "start": snap.flow_period.start.isoformat() if snap.flow_period.start else None,
                        "end": snap.flow_period.end.isoformat()})
        facts[pid] = {k: _fact(f, table) for k, f in snap.facts.items()}
        ext = None
        if snap.flow_period.basis == "annual":
            ext = _extended(companyfacts, research, snap, table)
            extended[pid] = ext
        prior = None
        if snap.flow_period.basis == "annual":
            idx = annual.index(snap)
            prior = annual[idx + 1] if idx + 1 < len(annual) else None
        metrics[pid] = _metric_rows(snap, table, ext, prior)
        scores[pid] = _score(snap)
    primary = research.annual[0]
    pid = _period_id(primary.flow_period)
    m = metrics[pid]
    instant = Period(None, primary.flow_period.end, "instant")
    _, scope = debt_scope(companyfacts, research.cik, research.currency, instant, as_of, ANNUAL_FORMS)

    def find_instant(concepts):
        return _find(companyfacts, research.cik, concepts, research.currency, instant, as_of, ANNUAL_FORMS)

    ladder = maturity_ladder(find_instant)
    for row in ladder:
        if row["source"]:
            row["source"] = {**row["source"], "ref": table.ref(find_instant((row["concept"],)).sources[0])}
    debt = primary.facts["debt"].value
    ext = extended.get(pid, {})
    ev = lambda k: (ext.get(k) or {}).get("value")  # noqa: E731
    cash = primary.facts["cash"].value
    liquid = None if cash is None else cash + (ev("short_term_investments") or 0)
    profile = risk_profile(debt, m["ebitda_proxy"]["value"], primary.facts["operating_cash_flow"].value, liquid)
    if debt is None and scope.completeness == "none":
        profile["basis"] = ("no borrowing tags reported — the issuer may be debt-free (common for cash-rich "
                            "technology and biotech companies); confirm in the debt note")
    total_liabilities = ev("total_liabilities")
    if total_liabilities is None and ev("total_assets") is not None and ev("equity") is not None:
        total_liabilities = ev("total_assets") - ev("equity")
    altman = altman_z_double_prime(primary.facts["current_assets"].value, primary.facts["current_liabilities"].value,
                                   ev("total_assets"), ev("retained_earnings"),
                                   primary.facts["operating_income"].value, ev("equity"), total_liabilities)
    coverage = {"available": [], "missing": []}
    for k, f in primary.facts.items():
        (coverage["available"] if f.value is not None else coverage["missing"]).append(
            k if f.value is not None else {"key": k, "reason": f.note})
    return {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": as_of.isoformat(),
        "versions": {"extractor": EXTRACTOR_VERSION, "screening": METHODOLOGY_VERSION,
                     "risk_profile": profile["method"]},
        "issuer": {"ticker": ticker, "cik": research.cik, "name": research.name,
                   "exchange": meta.get("exchange"), "hk": meta.get("hk"),
                   "sic": submissions.get("sic"), "sic_description": submissions.get("sicDescription"),
                   "sector": sector(submissions.get("sic"), ticker),
                   "fiscal_year_end": research.fiscal_year_end, "currency": research.currency,
                   "filer_category": submissions.get("category"),
                   "state": submissions.get("stateOfIncorporation"),
                   "country": (submissions.get("addresses", {}).get("business", {}) or {}).get("stateOrCountryDescription"),
                   "website": submissions.get("website") or None,
                   "sec_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={research.cik}",
                   "mcap_rank": meta.get("mcap_rank")},
        "primary": pid,
        "periods": periods,
        "facts": facts,
        "metrics": metrics,
        "score": scores,
        "extended": extended,
        "risk_profile": profile,
        "debt_scope": scope.as_dict(),
        "maturities": ladder,
        "altman": altman,
        "warnings": list(research.warnings),
        "coverage": coverage,
        "filings": {"annual": latest_filing(submissions, {"10-K", "20-F", "40-F"}),
                    "quarter": latest_filing(submissions, {"10-Q"})},
        "sources": table.rows,
        "formulas": {**FORMULAS, **EXTRA_FORMULAS},
    }


def summary_row(doc: dict) -> dict:
    """Compact row for the universe index / screener."""
    pid = doc["primary"]
    m = doc["metrics"][pid]
    f = doc["facts"][pid]
    val = lambda k: m.get(k, {}).get("value")  # noqa: E731
    rp = doc["risk_profile"]
    return {
        "t": doc["issuer"]["ticker"], "n": doc["issuer"]["name"], "s": doc["issuer"]["sector"],
        "hk": doc["issuer"]["hk"], "cur": doc["issuer"]["currency"], "fy": pid,
        "end": next(p["end"] for p in doc["periods"] if p["id"] == pid),
        "rev": f["revenue"]["value"], "ebitda": val("ebitda_proxy"), "debt": f["debt"]["value"],
        "cash": f["cash"]["value"], "fcf": val("fcf"), "lev": val("gross_leverage"),
        "nlev": val("net_leverage_adj"), "icov": val("interest_coverage"), "ecov": val("ebitda_coverage"),
        "cfod": val("cfo_to_debt"), "fcfd": val("fcf_to_debt"), "om": val("operating_margin"),
        "cr": val("current_ratio"), "g": val("revenue_growth"), "srf": val("shareholder_returns_to_fcf"),
        "tier": rp["overall"], "z": doc["altman"]["value"], "zone": doc["altman"]["zone"],
        "score": doc["score"][pid]["value"], "dc": doc["debt_scope"]["completeness"],
        "rank": doc["issuer"]["mcap_rank"], "nd": rp.get("net_debt"), "liq": rp.get("liquid_assets"),
        "rlev": rp["leverage"]["value"], "rcf": rp["cashflow"]["value"],
        "hd": (rp["headroom"].get("leverage") or {}).get("ebitda_decline_to_downgrade"),
        "hc": (rp["headroom"].get("cashflow") or {}).get("cfo_decline_to_downgrade"),
        "m12": next((r["value"] for r in doc.get("maturities", []) if r["bucket"] == "Next 12 months"), None),
    }
