"""Financial arithmetic only. No model calls, rounding, or source guessing."""
from __future__ import annotations

from .models import Metric, Snapshot

FORMULAS = {
    "ebitda_proxy": "Operating income + depreciation and amortization",
    "fcf": "Operating cash flow - cash capital expenditures",
    "net_debt": "Interest-bearing debt - unrestricted cash and cash equivalents",
    "gross_leverage": "Interest-bearing debt / EBITDA proxy (annual or TTM)",
    "net_leverage": "Net debt / EBITDA proxy (annual or TTM)",
    "interest_coverage": "Operating income / gross interest expense",
    "current_ratio": "Current assets / current liabilities",
    "fcf_to_debt": "Free cash flow (annual or TTM) / interest-bearing debt",
    "operating_margin": "Operating income / revenue",
}


def calculate(snapshot: Snapshot) -> dict[str, Metric]:
    def evidence(keys):
        return tuple(sorted({s.evidence_id for k in keys if k in snapshot.facts
                             for s in snapshot.facts[k].sources}))

    def derive(name, keys, operation, unit=None, denominator=None, annual=False):
        formula = FORMULAS.get(name, name.replace("_", " "))
        refs = evidence(keys)
        values = [snapshot.facts[k].value if k in snapshot.facts else None for k in keys]
        missing = [k for k, v in zip(keys, values) if v is None]
        unit = unit or snapshot.currency
        if missing:
            return Metric(name, None, unit, "missing", formula,
                          "Missing: " + ", ".join(missing), refs)
        if annual and snapshot.flow_period.basis not in {"annual", "ttm"}:
            return Metric(name, None, unit, "not_meaningful", formula,
                          "Requires annual or TTM flows; quarterly/YTD flows are not annualized.", refs)
        if denominator is not None and denominator(values) <= 0:
            return Metric(name, None, unit, "not_meaningful", formula,
                          "Zero or negative denominator; a conventional ratio is not meaningful.", refs)
        return Metric(name, operation(values), unit, "available", formula, "", refs)

    metrics = {k: derive(k, [k], lambda v: v[0]) for k in (
        "revenue", "operating_income", "interest_expense", "debt", "cash",
        "operating_cash_flow", "capex", "current_assets", "current_liabilities",
    )}
    metrics.update({
        "ebitda_proxy": derive("ebitda_proxy", ["operating_income", "depreciation_amortization"],
                               lambda v: v[0] + v[1]),
        "fcf": derive("fcf", ["operating_cash_flow", "capex"], lambda v: v[0] - v[1]),
        "net_debt": derive("net_debt", ["debt", "cash"], lambda v: v[0] - v[1]),
        "gross_leverage": derive("gross_leverage", ["debt", "operating_income", "depreciation_amortization"],
                                 lambda v: v[0] / (v[1] + v[2]), "x",
                                 denominator=lambda v: v[1] + v[2], annual=True),
        "net_leverage": derive("net_leverage", ["debt", "cash", "operating_income", "depreciation_amortization"],
                               lambda v: (v[0] - v[1]) / (v[2] + v[3]), "x",
                               denominator=lambda v: v[2] + v[3], annual=True),
        "interest_coverage": derive("interest_coverage", ["operating_income", "interest_expense"],
                                    lambda v: v[0] / v[1], "x", denominator=lambda v: v[1]),
        "current_ratio": derive("current_ratio", ["current_assets", "current_liabilities"],
                                lambda v: v[0] / v[1], "x", denominator=lambda v: v[1]),
        "fcf_to_debt": derive("fcf_to_debt", ["operating_cash_flow", "capex", "debt"],
                              lambda v: (v[0] - v[1]) / v[2], "ratio",
                              denominator=lambda v: v[2], annual=True),
        "operating_margin": derive("operating_margin", ["operating_income", "revenue"],
                                   lambda v: v[0] / v[1], "ratio", denominator=lambda v: v[1]),
    })
    return metrics


def revenue_growth(current: Snapshot, previous: Snapshot) -> Metric:
    a, b = current.facts.get("revenue"), previous.facts.get("revenue")
    refs = tuple(sorted({s.evidence_id for f in (a, b) if f for s in f.sources}))
    formula = "Current comparable revenue / prior-year comparable revenue - 1"
    if current.cik.lstrip("0") != previous.cik.lstrip("0") or current.currency != previous.currency:
        raise ValueError("Growth requires the same issuer and currency")
    p, q = current.flow_period, previous.flow_period
    days_apart = (p.end - q.end).days
    same_length = abs((p.end - p.start).days - (q.end - q.start).days) <= 14
    if p.basis != q.basis or not 330 <= days_apart <= 400 or not same_length:
        return Metric("revenue_growth", None, "ratio", "not_meaningful", formula,
                      "Periods must be comparable year-over-year fiscal durations.", refs)
    if a is None or b is None or a.value is None or b.value is None:
        return Metric("revenue_growth", None, "ratio", "missing", formula, "Revenue unavailable.", refs)
    if b.value <= 0:
        return Metric("revenue_growth", None, "ratio", "not_meaningful", formula,
                      "Prior revenue must be positive.", refs)
    return Metric("revenue_growth", a.value / b.value - 1, "ratio", "available", formula, "", refs)
