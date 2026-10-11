"""v0.1 transparent screening heuristic. Uncalibrated; not a rating/default probability."""
from __future__ import annotations

from dataclasses import dataclass

from .metrics import calculate
from .models import Snapshot

METHODOLOGY_VERSION = "screening-v0.1"
WEIGHTS = {"leverage": 30, "coverage": 25, "cash_flow": 20, "liquidity": 15, "profitability": 10}


@dataclass(frozen=True)
class Factor:
    name: str
    weight: int
    points: float | None
    explanation: str


@dataclass(frozen=True)
class HealthScore:
    value: float | None
    band: str
    coverage: int
    lower_bound: float
    upper_bound: float
    factors: tuple[Factor, ...]
    methodology: str = METHODOLOGY_VERSION


def _ramp(value, low, high):
    return max(0.0, min(100.0, 100 * (value - low) / (high - low)))


def score(snapshot: Snapshot) -> HealthScore:
    m = calculate(snapshot)
    value = lambda k: m[k].value
    debt, ebitda = value("debt"), value("ebitda_proxy")
    ebit, interest = value("operating_income"), value("interest_expense")
    fcf = value("fcf")
    annual = snapshot.flow_period.basis in {"annual", "ttm"}
    points = {k: None for k in WEIGHTS}
    notes = {
        "leverage": "Debt/EBITDA proxy: 100 at <=1x, linearly falling to 0 at >=5x.",
        "coverage": "Operating income/interest: 0 at <=1x, linearly rising to 100 at >=8x.",
        "cash_flow": "Annual/TTM FCF/debt: 0 at <=0%, linearly rising to 100 at >=40%.",
        "liquidity": "Current ratio: 0 at <=0.5x, linearly rising to 100 at >=2x.",
        "profitability": "Operating margin: 0 at <=0%, linearly rising to 100 at >=20%.",
    }
    if annual and debt is not None and ebitda is not None:
        if debt == 0:
            points["leverage"] = 100.0
            notes["leverage"] += " Confirmed zero debt: no debt burden."
        elif ebitda <= 0:
            points["leverage"] = 0.0
            notes["leverage"] += " Positive debt with nonpositive EBITDA: 0 points; ratio is NM."
        else:
            points["leverage"] = 100 - _ramp(debt / ebitda, 1, 5)
    if annual and ebit is not None and interest is not None:
        if interest > 0:
            points["coverage"] = _ramp(ebit / interest, 1, 8)
        elif debt == 0:
            points["coverage"] = 100.0 if ebit > 0 else 0.0
            notes["coverage"] += " Zero debt/interest: 100 only with positive operating earnings."
        else:
            notes["coverage"] += " Zero interest with debt is unresolved, not infinite coverage."
    if annual and fcf is not None and debt is not None:
        points["cash_flow"] = (_ramp(fcf / debt, 0, 0.4) if debt > 0
                               else (100.0 if fcf >= 0 else 0.0))
        if debt == 0:
            notes["cash_flow"] += " Confirmed zero debt: 100 with nonnegative FCF, otherwise 0."
    for key, metric, low, high in (("liquidity", "current_ratio", 0.5, 2),
                                   ("profitability", "operating_margin", 0, 0.2)):
        if value(metric) is not None:
            points[key] = _ramp(value(metric), low, high)
    factors = tuple(Factor(k, w, points[k], notes[k] +
                           (" Insufficient evidence/period for this factor." if points[k] is None else ""))
                    for k, w in WEIGHTS.items())
    coverage = sum(f.weight for f in factors if f.points is not None)
    lower = sum(f.weight * f.points / 100 for f in factors if f.points is not None)
    upper = lower + 100 - coverage
    # Unknown factors are never silently omitted and reweighted upward.
    if coverage < 100:
        return HealthScore(None, "Insufficient evidence", coverage, round(lower, 1), round(upper, 1), factors)
    result = round(lower, 1)
    band = "Strong" if result >= 80 else "Stable" if result >= 60 else "Watch" if result >= 40 else "Weak"
    return HealthScore(result, band, 100, result, result, factors)
