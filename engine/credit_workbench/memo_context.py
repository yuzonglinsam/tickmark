"""Analyst context passed to the memo model. Numbers inform reasoning; memo text stays digit-free."""
from __future__ import annotations


def analyst_context(d: dict) -> dict:
    """Qualitative + quantitative context from an issuer document (for the model's reasoning only)."""
    pid = d["primary"]
    m = d["metrics"][pid]
    trend = {}
    for key in ("revenue", "operating_income", "operating_cash_flow", "debt"):
        series = [(p["id"], d["facts"][p["id"]][key]["value"]) for p in d["periods"] if p["basis"] == "annual"]
        trend[key] = list(reversed(series))
    ext = d.get("extended", {}).get(pid, {})
    val = lambda k: (ext.get(k) or {}).get("value")  # noqa: E731
    return {
        "definitions": ("When discussing net leverage use net_debt_to_ebitda_net_of_cash_and_st_investments; "
                        "sector_medians.nlev uses the same definition. The bundle metric 'net_leverage' nets "
                        "cash only and should not be compared with the sector median."),
        "net_debt_to_ebitda_net_of_cash_and_st_investments": m.get("net_leverage_adj", {}).get("value"),
        "net_debt_net_of_cash_and_st_investments": m.get("net_debt_adj", {}).get("value"),
        "sector": d["issuer"]["sector"], "sic_description": d["issuer"]["sic_description"],
        "currency": d["issuer"]["currency"],
        "annual_trend_oldest_first": trend,
        "indicative_financial_risk_profile": {k: d["risk_profile"][k] for k in ("label", "basis", "leverage", "cashflow")},
        "threshold_headroom": d["risk_profile"]["headroom"],
        "sector_medians": d.get("peers", {}).get("median", {}),
        "sector_percentiles_higher_is_better": d.get("peers", {}).get("percentile", {}),
        "debt_definition_and_scope": d["debt_scope"],
        "debt_maturities": [(r["bucket"], r["value"]) for r in d.get("maturities", [])],
        "cash_uses": {"dividends": val("dividends"), "buybacks": val("buybacks"),
                      "acquisitions": val("acquisitions"), "free_cash_flow": m["fcf"]["value"]},
        "altman_z_double_prime_zone": d["altman"]["zone"],
    }
