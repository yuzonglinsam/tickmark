"""Reported-borrowings debt measure built only from SEC companyfacts tags.

Definition (stated everywhere it is shown):

    Debt = long-term borrowings including current maturities
         + short-term borrowings / commercial paper (where separately tagged)

Leases (finance and operating) are excluded and reported separately, because
companyfacts cannot tell whether a finance-lease liability is already inside a
debt line. Every component keeps its SEC source. A component that is not tagged
is never assumed to be zero: it is listed in ``scope.not_tagged`` so the UI can
show exactly how complete the figure is.

This is deliberately simpler and broader than the filing-reconciled measure in
``normalize._debt`` (used when filing XBRL reconciliation has been run), so the
same transparent definition can be applied to hundreds of issuers.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import Fact, Period

# Each long-term block is a list of concepts that must all come from one filing.
# Flags: (includes current maturities, includes short-term borrowings, includes leases)
LONG_TERM_BLOCKS: tuple[tuple[str, tuple[str, ...], tuple[bool, bool, bool]], ...] = (
    ("Total debt (long + short term)", ("DebtLongtermAndShorttermCombinedAmount",), (True, True, False)),
    ("Long-term debt incl. current, with finance leases",
     ("LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",), (True, False, True)),
    ("Long-term debt incl. current maturities", ("LongTermDebt",), (True, False, False)),
    ("Noncurrent + current long-term debt", ("LongTermDebtNoncurrent", "LongTermDebtCurrent"), (True, False, False)),
    ("Noncurrent long-term debt + current debt", ("LongTermDebtNoncurrent", "DebtCurrent"), (True, True, False)),
    ("Long-term debt and finance leases (noncurrent + current)",
     ("LongTermDebtAndCapitalLeaseObligations", "LongTermDebtAndCapitalLeaseObligationsCurrent"), (True, False, True)),
    ("Long-term debt and finance leases + current debt",
     ("LongTermDebtAndCapitalLeaseObligations", "DebtCurrent"), (True, True, True)),
    ("IFRS borrowings", ("ifrs-full:Borrowings",), (True, True, False)),
    ("IFRS noncurrent + current borrowings",
     ("ifrs-full:NoncurrentPortionOfNoncurrentBorrowings", "ifrs-full:CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings"),
     (True, True, False)),
    ("IFRS noncurrent + current borrowings",
     ("ifrs-full:NoncurrentBorrowings", "ifrs-full:CurrentBorrowings"), (True, True, False)),
    # Partial: current maturities are not separately tagged.
    ("Noncurrent long-term debt only", ("LongTermDebtNoncurrent",), (False, False, False)),
    ("Long-term debt and finance leases, noncurrent only",
     ("LongTermDebtAndCapitalLeaseObligations",), (False, False, True)),
)
# Instrument-level tags used only when no aggregate debt line is tagged. Within a
# group the first tagged concept is used (they overlap); groups are summed.
ITEMIZED_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Senior / unsecured notes", ("SeniorLongTermNotes", "SeniorNotes", "UnsecuredLongTermDebt",
                                  "LongTermNotesPayable", "UnsecuredDebt")),
    ("Bank loans", ("LongTermLoansFromBank", "SecuredLongTermDebt", "LongTermLineOfCredit",
                    "SecuredDebt", "LoansPayable")),
    ("Convertible notes", ("ConvertibleDebtNoncurrent", "ConvertibleNotesPayable",
                           "ConvertibleLongTermNotesPayable")),
    ("Current portion", ("LongTermDebtCurrent", "SeniorNotesCurrent", "ConvertibleNotesPayableCurrent",
                         "ConvertibleDebtCurrent", "LoansPayableCurrent")),
)
SHORT_TERM_OPTIONS: tuple[tuple[str, ...], ...] = (
    ("ShortTermBorrowings",),
    ("CommercialPaper", "OtherShortTermBorrowings"),
    ("CommercialPaper",),
    ("OtherShortTermBorrowings",),
    ("BankOverdrafts",),
)
LEASE_TAGS = ("FinanceLeaseLiability", "OperatingLeaseLiability", "ifrs-full:LeaseLiabilities")
REVIEWED_EXTENSIONS = ("ko:DisposalGroupIncludingDiscontinuedOperationCurrentMaturitiesOfLongTermDebt",
                       "ko:DisposalGroupIncludingDiscontinuedOperationLongTermDebt")
DEFINITION = ("Debt = long-term borrowings incl. current maturities + separately tagged short-term "
              "borrowings/commercial paper. Lease liabilities are not added on top (finance leases count only "
              "where the issuer's own debt line includes them).")


@dataclass
class DebtScope:
    method: str = "reported-tags"
    block: str = ""
    components: list[dict] = field(default_factory=list)
    not_tagged: list[str] = field(default_factory=list)
    leases: dict = field(default_factory=dict)
    completeness: str = "none"  # full, partial, none

    def as_dict(self) -> dict:
        return {"method": self.method, "block": self.block, "components": self.components,
                "not_tagged": self.not_tagged, "leases": self.leases,
                "completeness": self.completeness, "definition": DEFINITION}


def _component(fact: Fact, label: str) -> dict:
    s = fact.sources[0]
    return {"label": label, "concept": s.concept, "value": fact.value, "accession": s.accession,
            "url": s.url, "filed": s.filed_on.isoformat(), "form": s.form}


def reported_debt(find, period: Period, currency: str) -> tuple[Fact, DebtScope]:
    """``find(concepts) -> Fact | None`` is bound to one issuer/period/form set."""
    from .normalize import _missing  # local import: avoid circular module load

    scope = DebtScope()
    chosen: tuple[str, list[Fact], tuple[bool, bool, bool]] | None = None
    best_key = None
    for label, concepts, flags in LONG_TERM_BLOCKS:
        parts = [find((c,)) for c in concepts]
        if not all(p is not None and p.value is not None and p.value >= 0 for p in parts):
            continue
        if len({p.sources[0].accession for p in parts}) != 1:
            continue
        filed = max(p.sources[0].filed_on for p in parts)
        complete_rank = int(flags[0]) * 2 + int(flags[1])
        # Prefer the most recent filing; then the most complete block; then listed order.
        key = (filed, complete_rank)
        if best_key is None or key > best_key:
            best_key, chosen = key, (label, parts, flags)
    parts: list[Fact] = []
    itemized = False
    if not chosen:
        found_groups = []
        for glabel, concepts in ITEMIZED_GROUPS:
            for c in concepts:
                f = find((c,))
                if f is not None and f.value is not None and f.value > 0:
                    found_groups.append((glabel, f))
                    break
        if found_groups and any(g != "Current portion" for g, _ in found_groups):
            itemized = True
            scope.block = "Itemized instrument tags (no aggregate debt line tagged)"
            for glabel, f in found_groups:
                parts.append(f)
                scope.components.append(_component(f, glabel))
            scope.not_tagged.append("aggregate debt total (instrument tags may omit facilities)")
    if chosen:
        label, block_parts, (has_current, has_short, has_lease) = chosen
        scope.block = label
        parts.extend(block_parts)
        scope.components.extend(_component(p, label) for p in block_parts)
        if not has_current:
            scope.not_tagged.append("current maturities of long-term debt")
    else:
        has_short = False
    if not chosen or not has_short:
        for option in SHORT_TERM_OPTIONS:
            found = [find((c,)) for c in option]
            if all(f is not None and f.value is not None and f.value >= 0 for f in found):
                parts.extend(found)
                scope.components.extend(_component(f, "Short-term borrowings") for f in found)
                break
        else:
            scope.not_tagged.append("short-term borrowings / commercial paper (none tagged — may be nil)")
    for tag in REVIEWED_EXTENSIONS:
        ext = find((tag,))
        if ext is not None and ext.value and ext.value > 0:
            parts.append(ext)
            scope.components.append(_component(ext, "Disposal-group borrowings (reviewed)"))
    for tag in LEASE_TAGS:
        lease = find((tag,))
        if lease is not None and lease.value is not None:
            scope.leases[tag.split(":")[-1]] = _component(lease, "Lease liability (excluded)")
    if not chosen and itemized:
        scope.completeness = "partial"
    elif not chosen:
        if not parts:
            scope.completeness = "none"
            return (_missing(period, currency,
                             "No borrowing tags reported for this balance-sheet date. The issuer may have no "
                             "funded debt; confirm in the debt note."), scope)
        scope.completeness = "partial"
        scope.not_tagged.insert(0, "long-term debt")
    else:
        scope.completeness = "full" if chosen[2][0] else "partial"
    value = sum(p.value for p in parts)
    note = DEFINITION + f" Basis: {scope.block or 'short-term borrowings only'}."
    if scope.not_tagged:
        note += " Not separately tagged: " + "; ".join(scope.not_tagged) + "."
    fact = Fact(value, period, currency, tuple(s for p in parts for s in p.sources), "derived", note,
                tuple(s for p in parts for s in p.lineage))
    return fact, scope


def maturity_ladder(find) -> list[dict]:
    """Contractual principal maturities disclosed in the debt note (instant facts)."""
    tags = (("Next 12 months", "LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths"),
            ("Year 2", "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo"),
            ("Year 3", "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearThree"),
            ("Year 4", "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFour"),
            ("Year 5", "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFive"),
            ("After year 5", "LongTermDebtMaturitiesRepaymentsOfPrincipalAfterYearFive"))
    rows = []
    for label, tag in tags:
        fact = find((tag,))
        rows.append({"bucket": label, "concept": tag,
                     "value": fact.value if fact else None,
                     "source": _component(fact, label) if fact else None})
    if all(r["value"] is None for r in rows):
        return []
    return rows

