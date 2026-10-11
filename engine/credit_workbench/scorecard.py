"""Indicative financial-risk profile, rating-threshold headroom and distress screen.

Thresholds follow the *standard volatility* table published in S&P Global
Ratings' Corporate Methodology (a public document). Tickmark substitutes
CFO/Debt for FFO/Debt because FFO is not an XBRL concept. The output is an
**indicative financial risk profile**, not a credit rating, and it ignores
business risk, industry risk and all qualitative adjustments that a rating
committee applies.
"""
from __future__ import annotations

from dataclasses import dataclass

TIERS = ("Minimal", "Modest", "Intermediate", "Significant", "Aggressive", "Highly leveraged")
# Upper bounds of Debt/EBITDA for each tier (last tier is open-ended).
LEVERAGE_BOUNDS = (1.5, 2.0, 3.0, 4.0, 5.0)
# Lower bounds of CFO/Debt (FFO/Debt proxy) for each tier.
CASHFLOW_BOUNDS = (0.60, 0.45, 0.30, 0.20, 0.12)
METHOD_VERSION = "risk-profile-v2-net"


@dataclass(frozen=True)
class TierResult:
    tier: int | None  # 0 = Minimal … 5 = Highly leveraged
    value: float | None
    note: str


def leverage_tier(debt: float | None, ebitda: float | None) -> TierResult:
    if debt is None or ebitda is None:
        return TierResult(None, None, "Debt or EBITDA unavailable")
    if debt == 0:
        return TierResult(0, 0.0, "No reported borrowings")
    if ebitda <= 0:
        return TierResult(5, None, "Positive debt with non-positive EBITDA")
    ratio = debt / ebitda
    for i, bound in enumerate(LEVERAGE_BOUNDS):
        if ratio < bound:
            return TierResult(i, ratio, "")
    return TierResult(5, ratio, "")


def cashflow_tier(cfo: float | None, debt: float | None) -> TierResult:
    if cfo is None or debt is None:
        return TierResult(None, None, "CFO or debt unavailable")
    if debt == 0:
        return TierResult(0, None, "No reported borrowings")
    ratio = cfo / debt
    for i, bound in enumerate(CASHFLOW_BOUNDS):
        if ratio > bound:
            return TierResult(i, ratio, "")
    return TierResult(5, ratio, "")


def headroom(debt: float | None, ebitda: float | None, cfo: float | None) -> dict:
    """How far each core ratio can move before crossing into the next weaker tier.

    EBITDA decline to next tier: 1 - L/T   (L = Debt/EBITDA, T = tier ceiling)
    Debt capacity to next tier:  T/L - 1
    CFO decline to next tier:    1 - F/R   (R = CFO/Debt,   F = tier floor)
    """
    out: dict = {"leverage": None, "cashflow": None}
    lev = leverage_tier(debt, ebitda)
    if lev.tier is not None and lev.value and lev.tier < 5:
        ceiling = LEVERAGE_BOUNDS[lev.tier]
        floor = LEVERAGE_BOUNDS[lev.tier - 1] if lev.tier > 0 else None
        out["leverage"] = {
            "ratio": lev.value, "tier": lev.tier, "next_threshold": ceiling,
            "ebitda_decline_to_downgrade": 1 - lev.value / ceiling,
            "debt_increase_to_downgrade": ceiling / lev.value - 1,
            "ebitda_increase_to_upgrade": (lev.value / floor - 1) if floor else None,
            "upgrade_threshold": floor,
        }
    elif lev.tier == 5 and lev.value:
        floor = LEVERAGE_BOUNDS[-1]
        out["leverage"] = {"ratio": lev.value, "tier": 5, "next_threshold": None,
                           "ebitda_decline_to_downgrade": None, "debt_increase_to_downgrade": None,
                           "ebitda_increase_to_upgrade": lev.value / floor - 1, "upgrade_threshold": floor}
    cf = cashflow_tier(cfo, debt)
    if cf.tier is not None and cf.value is not None and cf.value > 0:
        floor = CASHFLOW_BOUNDS[cf.tier] if cf.tier < 5 else None
        better = CASHFLOW_BOUNDS[cf.tier - 1] if cf.tier > 0 else None
        out["cashflow"] = {
            "ratio": cf.value, "tier": cf.tier, "next_threshold": floor,
            "cfo_decline_to_downgrade": (1 - floor / cf.value) if floor else None,
            "cfo_increase_to_upgrade": (better / cf.value - 1) if better else None,
            "upgrade_threshold": better,
        }
    return out


def risk_profile(debt: float | None, ebitda: float | None, cfo: float | None,
                 liquid_assets: float | None = None) -> dict:
    """Profile on a net-debt basis: debt less cash and short-term investments (floored at zero).

    Rating agencies commonly net surplus cash for issuers with ample liquidity; Tickmark applies a
    simplified version without haircuts and shows the gross ratios alongside.
    """
    gross_debt = debt
    if debt is not None and liquid_assets is not None:
        debt = max(0.0, debt - liquid_assets)
    lev, cf = leverage_tier(debt, ebitda), cashflow_tier(cfo, debt)
    gross = {"leverage": leverage_tier(gross_debt, ebitda).value,
             "cashflow": cashflow_tier(cfo, gross_debt).value}
    tiers = [t.tier for t in (lev, cf) if t.tier is not None]
    overall = max(tiers) if tiers else None
    if len(tiers) == 2:
        basis = "weaker of Debt/EBITDA and CFO/Debt"
    elif tiers:
        basis = "single available ratio"
    elif gross_debt is None:
        basis = ("insufficient data: debt could not be assembled from standard XBRL tags "
                 "(see Debt & liquidity for what was found)")
    elif ebitda is None:
        basis = "insufficient data: EBITDA unavailable (operating income or D&A not tagged)"
    else:
        basis = "insufficient data"
    burning = (ebitda is not None and ebitda <= 0) or (cfo is not None and cfo < 0)
    if burning:
        overall = None
        basis = ("not meaningful: negative EBITDA or operating cash flow — assess liquidity runway "
                 "instead of leverage ratios")
    net_cash_note = "Net cash: cash and short-term investments exceed debt"
    lev_note = net_cash_note if (gross_debt or 0) > 0 and debt == 0 else lev.note
    cf_note = net_cash_note if (gross_debt or 0) > 0 and debt == 0 else cf.note
    return {
        "overall": overall, "label": TIERS[overall] if overall is not None else None, "basis": basis,
        "leverage": {"tier": lev.tier, "value": lev.value, "note": lev_note},
        "cashflow": {"tier": cf.tier, "value": cf.value, "note": cf_note},
        "headroom": headroom(debt, ebitda, cfo),
        "net_debt": debt, "gross_debt": gross_debt, "liquid_assets": liquid_assets,
        "gross": gross,
        "basis_note": ("Net debt = debt − cash − short-term investments (floored at zero)"
                       if liquid_assets is not None else "Gross debt (cash unavailable)"),
        "method": METHOD_VERSION,
    }


def altman_z_double_prime(current_assets, current_liabilities, total_assets, retained_earnings,
                          ebit, equity, total_liabilities) -> dict:
    """Altman Z'' (1995, non-manufacturing). Academic screen, not a default probability."""
    inputs = (current_assets, current_liabilities, total_assets, retained_earnings, ebit, equity,
              total_liabilities)
    if any(v is None for v in inputs) or total_assets <= 0 or total_liabilities <= 0:
        return {"value": None, "zone": None, "components": None}
    x1 = (current_assets - current_liabilities) / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = equity / total_liabilities
    z = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
    zone = "Safe" if z > 2.6 else "Grey" if z >= 1.1 else "Distress"
    return {"value": z, "zone": zone,
            "components": {"working_capital_to_assets": x1, "retained_earnings_to_assets": x2,
                           "ebit_to_assets": x3, "equity_to_liabilities": x4}}
