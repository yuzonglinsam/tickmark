"""Canonical money is in base currency units, never presentation millions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class Period:
    start: date | None
    end: date
    basis: str  # annual, quarter, ytd, ttm, instant

    def __post_init__(self):
        if self.basis not in {"annual", "quarter", "ytd", "ttm", "instant"}:
            raise ValueError("Unknown period basis")
        if self.basis == "instant":
            if self.start is not None:
                raise ValueError("Instant facts have no start date")
        elif self.start is None or self.start > self.end:
            raise ValueError("Duration facts require an ordered start/end")


@dataclass(frozen=True)
class Source:
    evidence_id: str
    url: str
    accession: str
    form: str
    filed_on: date
    concept: str

    def __post_init__(self):
        if not all((self.evidence_id, self.url, self.accession, self.form, self.concept)):
            raise ValueError("Evidence requires identity, location and filing metadata")


@dataclass(frozen=True)
class Fact:
    value: float | None
    period: Period
    unit: str
    sources: tuple[Source, ...] = ()
    status: str = "reported"
    note: str = ""
    lineage: tuple[Source, ...] = ()  # superseded observations, never current metric evidence

    def __post_init__(self):
        if self.status not in {"reported", "derived", "missing", "scenario"}:
            raise ValueError("Unknown fact status")
        if not self.unit:
            raise ValueError("Unit is required")
        if self.value is None:
            if self.status != "missing" or not self.note:
                raise ValueError("Missing values require an explicit explanation")
        elif not isfinite(self.value) or self.status == "missing" or not self.sources:
            raise ValueError("Every finite value must have evidence and a valid status")
        if self.status in {"derived", "scenario"} and not self.note:
            raise ValueError("Derived/scenario facts require a method or assumption")


FLOW_KEYS = frozenset({
    "revenue", "operating_income", "depreciation_amortization",
    "operating_cash_flow", "capex", "interest_expense",
})
STOCK_KEYS = frozenset({"debt", "cash", "current_assets", "current_liabilities"})
NONNEGATIVE_KEYS = frozenset({
    "capex", "interest_expense", "depreciation_amortization", "debt", "cash",
    "current_assets", "current_liabilities",
})


@dataclass(frozen=True)
class Snapshot:
    cik: str
    ticker: str
    currency: str
    flow_period: Period
    as_of: date
    facts: Mapping[str, Fact]

    def __post_init__(self):
        if not self.cik.isdigit() or not 1 <= len(self.cik) <= 10:
            raise ValueError("CIK must be one to ten digits")
        if not self.ticker or len(self.currency) != 3:
            raise ValueError("Ticker and currency are required")
        if self.flow_period.basis == "instant" or self.flow_period.end > self.as_of:
            raise ValueError("Invalid snapshot period/as-of date")
        unknown = self.facts.keys() - FLOW_KEYS - STOCK_KEYS
        if unknown:
            raise ValueError(f"Unmapped canonical fields: {sorted(unknown)}")
        for name, fact in self.facts.items():
            if fact.unit != self.currency:
                raise ValueError(f"{name}: mixed currencies or scaled units")
            expected = (self.flow_period if name in FLOW_KEYS else
                        Period(None, self.flow_period.end, "instant"))
            if fact.period != expected:
                raise ValueError(f"{name}: inconsistent fiscal period")
            if any(s.filed_on > self.as_of for s in fact.sources + fact.lineage):
                raise ValueError(f"{name}: evidence was not available as of the analysis")
            if name in NONNEGATIVE_KEYS and fact.value is not None and fact.value < 0:
                raise ValueError(f"{name}: normalize a validated outflow/magnitude upstream")
        object.__setattr__(self, "facts", MappingProxyType(dict(self.facts)))


@dataclass(frozen=True)
class Metric:
    name: str
    value: float | None
    unit: str
    status: str  # available, missing, not_meaningful
    formula: str
    explanation: str
    evidence_ids: tuple[str, ...] = ()
