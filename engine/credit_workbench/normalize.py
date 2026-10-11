"""Conservative SEC companyfacts normalization with exact fiscal contexts.

Only entity-wide, standard taxonomy facts are eligible here. Unsupported custom
concepts stay missing until a filing-level XBRL reconciliation is available.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from dataclasses import replace
from datetime import date
from math import isfinite
from typing import Iterable

from .debt import reported_debt
from .models import FLOW_KEYS, STOCK_KEYS, Fact, Period, Snapshot, Source

EXTRACTOR_VERSION = "companyfacts-v0.6"
ANNUAL_FORMS = {"10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"}
QUARTER_FORMS = {"10-Q", "10-Q/A"}
FINANCIAL_FORMS = ANNUAL_FORMS | QUARTER_FORMS

# Alternatives are tried in order; overlapping tags are never added together.
CONCEPTS = {
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax", "ifrs-full:Revenue", "ifrs-full:RevenueFromContractsWithCustomers"),
    "operating_income": ("OperatingIncomeLoss", "ifrs-full:ProfitLossFromOperatingActivities"),
    "depreciation_amortization": ("DepreciationDepletionAndAmortization",
                                   "DepreciationAndAmortization", "DepreciationAmortizationAndAccretionNet",
                                   "ifrs-full:DepreciationAndAmortisationExpense",
                                   "ifrs-full:AdjustmentsForDepreciationAndAmortisationExpense"),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities", "ifrs-full:CashFlowsFromUsedInOperatingActivities"),
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets",
              "ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
              "ifrs-full:PurchaseOfPropertyPlantAndEquipment"),
    "interest_expense": ("InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt",
                         "InterestAndDebtExpense", "ifrs-full:InterestExpense", "ifrs-full:FinanceCosts"),
    "cash": ("CashAndCashEquivalentsAtCarryingValue", "ifrs-full:CashAndCashEquivalents"),
    "current_assets": ("AssetsCurrent", "ifrs-full:CurrentAssets"),
    "current_liabilities": ("LiabilitiesCurrent", "ifrs-full:CurrentLiabilities"),
}
PRETAX = ("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
          "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
          "ifrs-full:ProfitLossBeforeTax")
DEBT_TOTALS = ("LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
               "LongTermDebt")
DEBT_COMPONENTS = ("LongTermDebtCurrent", "LongTermDebtNoncurrent")


@dataclass(frozen=True)
class NormalizedResearch:
    name: str
    cik: str
    ticker: str
    currency: str
    annual: tuple[Snapshot, ...]
    quarter: Snapshot | None
    ttm: Snapshot | None
    warnings: tuple[str, ...]
    fiscal_year_end: str


def eligibility(submissions: dict) -> tuple[bool, str]:
    sic = str(submissions.get("sic") or "")
    name = submissions.get("name") or "This issuer"
    if not sic.isdigit():
        return False, f"{name}: SEC industry classification is unavailable; corporate methodology needs review."
    code = int(sic)
    if 6000 <= code < 6800 and code != 6798:
        return False, f"{name}: SIC {sic} is a financial institution/fund; the corporate debt methodology does not apply."
    if code == 6798:
        return False, f"{name}: SIC 6798 is a REIT; lease and property metrics require a separate methodology."
    return True, ""


def _observations(companyfacts: dict, concept: str, currency: str) -> list[dict]:
    taxonomies = companyfacts.get("facts", {})
    if ":" in concept:
        namespace, tag = concept.split(":", 1)
        return taxonomies.get(namespace, {}).get(tag, {}).get("units", {}).get(currency, [])
    return taxonomies.get("us-gaap", {}).get(concept, {}).get("units", {}).get(currency, [])


def _rows(companyfacts: dict, concept: str, currency: str, *, end: date,
          start: date | None, as_of: date, forms: set[str]) -> list[dict]:
    result = []
    for row in _observations(companyfacts, concept, currency):
        try:
            if (date.fromisoformat(row["end"]) != end or
                (date.fromisoformat(row["start"]) if "start" in row else None) != start or
                date.fromisoformat(row["filed"]) > as_of or row["form"] not in forms or
                not isinstance(row["val"], (int, float)) or isinstance(row["val"], bool) or
                not isfinite(row['val']) or
                not row.get("accn")):
                continue
        except (KeyError, ValueError, TypeError):
            continue
        result.append(row)
    # Latest valid filing for the exact observation. Amendments with no financial
    # tag cannot remove an earlier reported fact.
    return sorted(result, key=lambda r: (r["filed"], r["accn"]), reverse=True)


def _source(cik: str, concept: str, row: dict, start: date | None, currency: str) -> Source:
    accession = row["accn"]
    folder = accession.replace("-", "")
    url = row.get("_url") or f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{folder}/"
    context = row.get("_context_ref", "")
    period_id = f"{start.isoformat() if start else 'instant'}:{row['end']}"
    return Source(f"{cik}:{accession}:{concept}:{period_id}:{currency}:{context}", url,
                  accession, row["form"], date.fromisoformat(row["filed"]), concept)


def _find(companyfacts: dict, cik: str, concepts: Iterable[str], currency: str,
          period: Period, as_of: date, forms: set[str], note: str = "") -> Fact | None:
    candidates = []
    for priority, concept in enumerate(concepts):
        rows = _rows(companyfacts, concept, currency, end=period.end, start=period.start,
                     as_of=as_of, forms=forms)
        if rows:
            candidates.append((rows[0]["filed"], -priority, concept, rows))
    if not candidates:
        return None
    _, _, concept, rows = max(candidates, key=lambda item: item[:2])
    row = rows[0]
    lineage = tuple(_source(cik, concept, prior, period.start, currency)
                    for prior in rows[1:] if prior["val"] != row["val"])
    return Fact(float(row["val"]), period, currency,
                (_source(cik, concept, row, period.start, currency),),
                note=note or f"SEC {concept}; exact reported fiscal context.",
                lineage=lineage)


def _missing(period: Period, currency: str, reason: str) -> Fact:
    return Fact(None, period, currency, status="missing", note=reason)


def _flow(companyfacts: dict, cik: str, key: str, currency: str, period: Period,
          as_of: date, forms: set[str]) -> Fact:
    concepts = CONCEPTS[key]
    note = ("Cash-flow statement D&A proxy; may differ from income-statement scope. "
            "Do not treat as issuer-adjusted EBITDA." if key == "depreciation_amortization" else "")
    fact = _find(companyfacts, cik, concepts, currency, period, as_of, forms, note)
    if fact is None and key == "depreciation_amortization":
        pairs = (("Depreciation", "AmortizationOfIntangibleAssets"),
                 ("ifrs-full:DepreciationExpense", "ifrs-full:AmortisationExpense"))
        for pair in pairs:
            parts = [_find(companyfacts, cik, (tag,), currency, period, as_of, forms) for tag in pair]
            if (all(p and p.value >= 0 for p in parts) and
                    len({s.accession for p in parts for s in p.sources}) == 1):
                fact = Fact(sum(p.value for p in parts), period, currency,
                            tuple(s for p in parts for s in p.sources), "derived",
                            "Reported depreciation + reported intangible amortization from one filing. "
                            "Scope is a proxy; other amortization may be excluded. No impairment or SBC is added.",
                            tuple(s for p in parts for s in p.lineage))
                break
    if fact is None and key == "depreciation_amortization":
        dep = _find(companyfacts, cik, ("Depreciation", "DepreciationNonproduction",
                                        "ifrs-full:DepreciationExpense"), currency, period, as_of, forms)
        if dep is not None and dep.value is not None and dep.value >= 0:
            fact = Fact(dep.value, period, currency, dep.sources, "derived",
                        "Depreciation only: intangible amortization was not separately tagged, so the EBITDA "
                        "proxy may be understated (leverage conservatively overstated).", dep.lineage)
    if fact is None and key == "interest_expense":
        paid = _find(companyfacts, cik, ("InterestPaidNet", "InterestPaid"), currency, period, as_of, forms)
        if paid is not None and paid.value is not None and paid.value >= 0:
            fact = Fact(paid.value, period, currency, paid.sources, "derived",
                        "Cash interest paid (cash-flow supplemental disclosure) used as an interest-cost proxy; "
                        "no income-statement interest expense tag was reported.", paid.lineage)
    if fact is None and key == "operating_income":
        pretax = _find(companyfacts, cik, PRETAX, currency, period, as_of, forms)
        interest = _flow(companyfacts, cik, "interest_expense", currency, period, as_of, forms)
        if pretax is not None and interest.value is not None:
            fact = Fact(pretax.value + interest.value, period, currency, pretax.sources + interest.sources,
                        "derived", "EBIT proxy = pre-tax income + interest expense; no operating-income tag "
                        "was reported. Includes non-operating items.", pretax.lineage + interest.lineage)
    if fact is None:
        return _missing(period, currency, f"No exact-period entity-wide SEC tag for {key}; filing-level review required.")
    if key in {"capex", "depreciation_amortization", "interest_expense"} and fact.value < 0:
        return _missing(period, currency, f"SEC {key} has a negative sign; outflow/magnitude not verified.")
    return fact


def _debt(companyfacts: dict, cik: str, currency: str, period: Period,
          as_of: date, forms: set[str]) -> Fact:
    if "_filing_scope_checked" not in companyfacts:
        return debt_scope(companyfacts, cik, currency, period, as_of, forms)[0]
    return _reconciled_debt(companyfacts, cik, currency, period, as_of, forms)


def debt_scope(companyfacts: dict, cik: str, currency: str, period: Period,
               as_of: date, forms: set[str]):
    """Broad, transparent reported-borrowings measure (see ``debt.py``)."""
    def find(concepts):
        return _find(companyfacts, cik, concepts, currency, period, as_of, forms)
    return reported_debt(find, period, currency)


def _reconciled_debt(companyfacts: dict, cik: str, currency: str, period: Period,
                     as_of: date, forms: set[str]) -> Fact:
    # A reported total including current maturities is preferred over components.
    # The noncurrent "LongTermDebtAndCapitalLeaseObligations" tag is deliberately
    # excluded: KO's FY2025 filing, for example, reports a separate current portion.
    base = None
    finance_included = False
    for concept in DEBT_TOTALS:
        fact = _find(companyfacts, cik, (concept,), currency, period, as_of, forms)
        if fact and fact.value >= 0:
            base = fact
            finance_included = concept.startswith("LongTermDebtAndCapitalLease")
            break
    if base is None:
        components = [_find(companyfacts, cik, (concept,), currency, period, as_of, forms)
                      for concept in DEBT_COMPONENTS]
        if all(f and f.value >= 0 for f in components):
            accessions = {s.accession for f in components for s in f.sources}
            if len(accessions) == 1:
                base = Fact(sum(f.value for f in components), period, currency,
                            tuple(s for f in components for s in f.sources), "derived",
                            "Current + noncurrent long-term debt from one filing.")
    if base is None:
        return _missing(period, currency,
                        "No complete interest-bearing debt total including current maturities was verified.")
    accession = base.sources[0].accession
    if accession not in companyfacts.get('_filing_scope_checked', []):
        return _missing(period, currency, "Borrowing tags found, but complete debt scope is not reconciled. Use filing XBRL reconciliation before leverage/scoring.")
    unresolved = [r['concept'] for r in companyfacts.get('_unknown_debt', []) if r['end'] == period.end.isoformat()]
    if unresolved:
        return _missing(period, currency, "Custom borrowing concepts require review: " + ', '.join(sorted(set(unresolved))))
    parts = [base]
    short_total = _find(companyfacts, cik, ("ShortTermBorrowings",), currency,
                        period, as_of, forms)
    if short_total and short_total.sources[0].accession == accession:
        parts.append(short_total)
    else:
        short_parts = []
        for concept in ("CommercialPaper", "OtherShortTermBorrowings"):
            part = _find(companyfacts, cik, (concept,), currency, period, as_of, forms)
            if part and part.sources[0].accession == accession:
                short_parts.append(part)
        if len(short_parts) < 2:
            return _missing(period, currency, "Complete short-term borrowing scope is unresolved; absent commercial paper/other borrowing tags are not inferred zero.")
        parts.extend(short_parts)
    if not finance_included:
        lease = _find(companyfacts, cik, ("FinanceLeaseLiability",), currency,
                      period, as_of, forms)
        if lease and lease.sources[0].accession == accession:
            parts.append(lease)
        else:
            return _missing(period, currency, "Long-term borrowing verified, but finance-lease completeness is unresolved; absent tags are not inferred zero.")
    for tag in ('ko:DisposalGroupIncludingDiscontinuedOperationCurrentMaturitiesOfLongTermDebt',
                'ko:DisposalGroupIncludingDiscontinuedOperationLongTermDebt'):
        part = _find(companyfacts, cik, (tag,), currency, period, as_of, forms)
        if part and part.sources[0].accession == accession:
            parts.append(part)
    if any(f.value < 0 for f in parts):
        return _missing(period, currency, "Debt component has an unverified negative sign.")
    return Fact(sum(f.value for f in parts), period, currency,
                tuple(s for f in parts for s in f.sources), "derived",
                "Sum of non-overlapping reported long-term borrowing, reported short-term "
                "borrowing/commercial paper and finance lease tags from one filing. "
                "Reviewed disposal-group borrowing extensions are included where reported. "
                "Unavailable custom debt concepts require debt-note review.",
                tuple(s for f in parts for s in f.lineage))


def _snapshot(companyfacts: dict, cik: str, ticker: str, currency: str,
              period: Period, as_of: date, forms: set[str]) -> Snapshot:
    facts = {key: _flow(companyfacts, cik, key, currency, period, as_of, forms)
             for key in FLOW_KEYS}
    instant = Period(None, period.end, "instant")
    for key in STOCK_KEYS - {"debt"}:
        facts[key] = (_find(companyfacts, cik, CONCEPTS[key], currency, instant, as_of, forms)
                      or _missing(instant, currency, f"No exact-date entity-wide SEC tag for {key}."))
    if facts["cash"].value is None:
        alt = _find(companyfacts, cik, ("CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
                                        "CashAndDueFromBanks"), currency, instant, as_of, forms)
        if alt is not None and alt.value is not None and alt.value >= 0:
            facts["cash"] = Fact(alt.value, instant, currency, alt.sources, "derived",
                                 "Cash incl. restricted cash (no unrestricted cash tag reported); may overstate "
                                 "freely available cash.", alt.lineage)
    facts["debt"] = _debt(companyfacts, cik, currency, instant, as_of, forms)
    return Snapshot(cik, ticker, currency, period, as_of, facts)


def _difference(current: Fact, previous: Fact, period: Period, key: str,
                operation: str) -> Fact:
    if current.value is None or previous.value is None:
        return _missing(period, current.unit, f"{key}: exact comparable YTD inputs are unavailable.")
    if {s.concept for s in current.sources} != {s.concept for s in previous.sources}:
        return _missing(period, current.unit, f"{key}: YTD concepts differ; accounting comparability needs review.")
    value = current.value - previous.value
    if key in {"capex", "depreciation_amortization", "interest_expense"} and value < 0:
        return _missing(period, current.unit, f"{key}: YTD difference has an unverified negative magnitude.")
    return Fact(value, period, current.unit, current.sources + previous.sources, "derived",
                f"{operation}: {current.period.start} to {current.period.end} less "
                f"{previous.period.start} to {previous.period.end}; identical currency and standard tag.",
                current.lineage + previous.lineage)


def _closest_prior_quarter(submissions: dict, end: date, as_of: date) -> date | None:
    choices = [prior for prior in _filing_ends(submissions, QUARTER_FORMS, as_of)
               if 330 <= (end - prior).days <= 400]
    return min(choices, key=lambda d: abs((end - d).days - 365)) if choices else None


def _discrete_quarter(companyfacts: dict, submissions: dict, cik: str, ticker: str,
                      currency: str, end: date, start: date, fiscal_start: date,
                      as_of: date) -> Snapshot:
    period = Period(start, end, "quarter")
    result = _snapshot(companyfacts, cik, ticker, currency, period, as_of, QUARTER_FORMS)
    if start == fiscal_start:
        return result
    prior_end = date.fromordinal(start.toordinal() - 1)
    current_ytd = Period(fiscal_start, end, "ytd")
    prior_ytd = Period(fiscal_start, prior_end, "ytd")
    facts = dict(result.facts)
    for key in FLOW_KEYS:
        if facts[key].value is not None:
            continue
        current = _flow(companyfacts, cik, key, currency, current_ytd, as_of, QUARTER_FORMS)
        previous = _flow(companyfacts, cik, key, currency, prior_ytd, as_of, QUARTER_FORMS)
        facts[key] = _difference(current, previous, period, key, "Discrete quarter")
    return replace(result, facts=facts)


def _build_ttm(companyfacts: dict, submissions: dict, annual: Snapshot,
               quarter: Snapshot, as_of: date) -> Snapshot | None:
    prior_end = _closest_prior_quarter(submissions, quarter.flow_period.end, as_of)
    if prior_end is None:
        return None
    fiscal_start = date.fromordinal(annual.flow_period.end.toordinal() + 1)
    current_ytd = Period(fiscal_start, quarter.flow_period.end, "ytd")
    prior_ytd = Period(annual.flow_period.start, prior_end, "ytd")
    if abs((current_ytd.end - current_ytd.start).days -
           (prior_ytd.end - prior_ytd.start).days) > 14:
        return None
    period = Period(date.fromordinal(prior_end.toordinal() + 1),
                    quarter.flow_period.end, "ttm")
    if not 330 <= (period.end - period.start).days + 1 <= 400:
        return None
    facts = {key: fact for key, fact in quarter.facts.items()
             if key in STOCK_KEYS}
    for key in FLOW_KEYS:
        full = annual.facts[key]
        current = _flow(companyfacts, annual.cik, key, annual.currency,
                        current_ytd, as_of, QUARTER_FORMS)
        previous = _flow(companyfacts, annual.cik, key, annual.currency,
                         prior_ytd, as_of, QUARTER_FORMS)
        if None in (full.value, current.value, previous.value):
            facts[key] = _missing(period, annual.currency,
                                  f"{key}: FY + current YTD − prior YTD lacks a compatible input.")
            continue
        if len({tuple(sorted({s.concept for s in fact.sources})) for fact in (full, current, previous)}) != 1:
            facts[key] = _missing(period, annual.currency,
                                  f"{key}: TTM inputs use different SEC concepts; reconciliation required.")
            continue
        value = full.value + current.value - previous.value
        if key in {"capex", "depreciation_amortization", "interest_expense"} and value < 0:
            facts[key] = _missing(period, annual.currency,
                                  f"{key}: TTM magnitude is negative; reconciliation required.")
            continue
        facts[key] = Fact(value, period, annual.currency,
                          full.sources + current.sources + previous.sources, "derived",
                          "TTM = latest fiscal year + current fiscal YTD − prior comparable fiscal YTD. "
                          "All input contexts and accessions are retained.",
                          full.lineage + current.lineage + previous.lineage)
    if all(facts[k].value is None for k in ("revenue", "operating_income",
                                             "operating_cash_flow")):
        return None
    return Snapshot(annual.cik, annual.ticker, annual.currency, period, as_of, facts)


def _filing_ends(submissions: dict, forms: set[str], as_of: date) -> list[date]:
    recent = submissions.get("filings", {}).get("recent", {})
    result = set()
    for form, report, filed in zip(recent.get("form", []), recent.get("reportDate", []),
                                   recent.get("filingDate", [])):
        try:
            if form in forms and date.fromisoformat(filed) <= as_of:
                result.add(date.fromisoformat(report))
        except ValueError:
            continue
    return sorted(result, reverse=True)


def _period_start(companyfacts: dict, end: date, currency: str, as_of: date,
                  forms: set[str], min_days: int, max_days: int) -> date | None:
    starts = Counter()
    for concept in CONCEPTS["revenue"] + CONCEPTS["operating_income"]:
        for row in _observations(companyfacts, concept, currency):
            try:
                start = date.fromisoformat(row["start"])
                days = (end - start).days + 1
                if (row["end"] == end.isoformat() and min_days <= days <= max_days and
                    row["form"] in forms and date.fromisoformat(row["filed"]) <= as_of):
                    starts[start] += 1
            except (KeyError, ValueError, TypeError):
                continue
    return starts.most_common(1)[0][0] if starts else None


def _currency(companyfacts: dict) -> str:
    # Select an actual reporting currency from revenue facts, not a UI default.
    for namespace in ("us-gaap", "ifrs-full"):
        facts = companyfacts.get("facts", {}).get(namespace, {})
        for concept in CONCEPTS["revenue"]:
            if ":" in concept:
                ns, concept = concept.split(":", 1)
                if ns != namespace:
                    continue
            units = facts.get(concept, {}).get("units", {})
            currencies = [u for u in units if len(u) == 3 and u.isalpha()]
            if currencies:
                return max(currencies, key=lambda unit: len(units[unit]))
    raise ValueError("No standard entity-wide revenue currency found; filing-level XBRL review required.")


def normalize(submissions: dict, companyfacts: dict, ticker: str,
              as_of: date | None = None) -> NormalizedResearch:
    as_of = as_of or date.today()
    cik = str(submissions["cik"]).zfill(10)
    if str(companyfacts.get("cik", "")).zfill(10) != cik:
        raise ValueError("SEC submissions and companyfacts CIKs differ")
    eligible, reason = eligibility(submissions)
    if not eligible:
        raise ValueError(reason)
    currency = _currency(companyfacts)
    annual = []
    for end in _filing_ends(submissions, ANNUAL_FORMS, as_of):
        start = _period_start(companyfacts, end, currency, as_of, ANNUAL_FORMS, 330, 400)
        if start:
            annual.append(_snapshot(companyfacts, cik, ticker, currency,
                                    Period(start, end, "annual"), as_of, ANNUAL_FORMS))
        if len(annual) == 3:
            break
    if not annual:
        raise ValueError("No exact annual SEC companyfacts period found; filing-level review required.")
    warnings = ["Companyfacts covers standard entity-wide tags; custom debt and disclosure notes require filing review."]
    latest_annual = _filing_ends(submissions, ANNUAL_FORMS, as_of)[0]
    if annual[0].flow_period.end < latest_annual:
        warnings.append(f"Latest annual report date {latest_annual} is not reconciled; displayed annual data ends "
                        f"{annual[0].flow_period.end}. Use filing XBRL reconciliation.")
    if any('Financing' in tag and 'Interest' in tag for tag in companyfacts.get('facts', {}).get('us-gaap', {})):
        warnings.append("The filing contains financing-business interest concepts. Mixed industrial/financial "
                        "operations need separate segment review; a consolidated corporate screen can be misleading.")
    if "ifrs-full" in companyfacts.get("facts", {}):
        warnings.append("IFRS annual financials are supported. IFRS lease liabilities cannot automatically be "
                        "split into US-GAAP operating/finance categories; unsupported debt and quarterly fields remain N/A.")
    if any(s.facts["debt"].value is not None for s in annual):
        warnings.append("Reported long-term debt tags may omit commercial paper or separate finance leases; verify debt notes before relying on the screening score.")
    # Quarterly and TTM are assembled separately; an unsupported flow remains N/A.
    quarter = None
    ttm = None
    for end in _filing_ends(submissions, QUARTER_FORMS, as_of):
        if end <= annual[0].flow_period.end:
            continue
        start = _period_start(companyfacts, end, currency, as_of, QUARTER_FORMS, 60, 120)
        if start:
            quarter = _snapshot(companyfacts, cik, ticker, currency,
                                Period(start, end, "quarter"), as_of, QUARTER_FORMS)
            break
    if quarter:
        fiscal_start = date.fromordinal(annual[0].flow_period.end.toordinal() + 1)
        quarter = _discrete_quarter(companyfacts, submissions, cik, ticker, currency,
                                    quarter.flow_period.end, quarter.flow_period.start,
                                    fiscal_start, as_of)
        ttm = _build_ttm(companyfacts, submissions, annual[0], quarter, as_of)
        if ttm is None:
            warnings.append("A comparable TTM series could not be reconciled; latest quarter and FY remain separate.")
    else:
        # The latest annual filing can supply Q4 without annualizing any quarter.
        prior_quarters = [end for end in _filing_ends(submissions, QUARTER_FORMS, as_of)
                          if 60 <= (annual[0].flow_period.end - end).days <= 120]
        if prior_quarters:
            prior_end = prior_quarters[0]
            period = Period(date.fromordinal(prior_end.toordinal() + 1), annual[0].flow_period.end, 'quarter')
            quarter = _snapshot(companyfacts, cik, ticker, currency, period, as_of, ANNUAL_FORMS)
            facts = dict(quarter.facts)
            prior_ytd = Period(annual[0].flow_period.start, prior_end, 'ytd')
            for key in FLOW_KEYS:
                if facts[key].value is None:
                    ytd = _flow(companyfacts, cik, key, currency, prior_ytd, as_of, FINANCIAL_FORMS)
                    facts[key] = _difference(annual[0].facts[key], ytd, period, key, 'Q4 = FY − nine-month YTD')
            quarter = replace(quarter, facts=facts)
    quarter_filings = [end for end in _filing_ends(submissions, QUARTER_FORMS, as_of)
                       if end > annual[0].flow_period.end]
    if quarter_filings and (quarter is None or quarter.flow_period.end < quarter_filings[0]):
        latest = quarter_filings[0]
        used = quarter.flow_period.end if quarter else annual[0].flow_period.end
        warnings.append(f"Latest 10-Q report date {latest} has no exact standard quarter facts; "
                        f"displayed flow data ends {used}. Filing-level review is pending.")
    return NormalizedResearch(submissions.get("name") or ticker, cik, ticker, currency,
                              tuple(annual), quarter, ttm, tuple(warnings),
                              str(submissions.get("fiscalYearEnd") or "Unknown"))
