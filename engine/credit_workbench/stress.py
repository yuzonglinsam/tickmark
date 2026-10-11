"""Static sensitivity: keep debt, cash, capex and D&A fixed; no balance-sheet forecast."""
from __future__ import annotations

from dataclasses import replace
from math import isfinite

from .models import Snapshot


def stress(snapshot: Snapshot, *, ebit_change: float = 0, interest_change: float = 0,
           cash_flow_change: float = 0) -> Snapshot:
    """Each signed change is a fraction of ABS(base), so negatives behave sensibly.

    -0.2 means deterioration by 20% of |base|. For positive interest expense,
    +0.2 means expense rises 20%. A zero base remains zero; UI must explain this.
    """
    changes = {"operating_income": ebit_change, "interest_expense": interest_change,
               "operating_cash_flow": cash_flow_change}
    if any(changes.values()) and any(f.status == "scenario" for f in snapshot.facts.values()):
        raise ValueError("Apply stress to the base snapshot, not an existing scenario")
    facts = dict(snapshot.facts)
    for key, change in changes.items():
        if not isfinite(change) or not -1 <= change <= 2:
            raise ValueError("Stress changes must be between -100% and +200%")
        fact = facts.get(key)
        if change == 0 or fact is None or fact.value is None:
            continue
        facts[key] = replace(fact, value=fact.value + abs(fact.value) * change,
                             status="scenario", note=f"Base {fact.value}; change {change:+.1%} of |base|. "
                             "Other inputs held constant; not a cash-balance forecast.")
    return replace(snapshot, facts=facts)
