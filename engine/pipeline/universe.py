"""Select the coverage universe: large-cap US-listed non-financial SEC filers.

The SEC ticker/exchange index is ordered approximately by market value. We walk
it in order, keep NYSE/Nasdaq listings, de-duplicate share classes by CIK, and
drop issuers outside the corporate credit methodology (banks, insurers, funds,
REITs) using the SEC SIC code. A curated list of China-based issuers that are
also listed in Hong Kong is always added so the HK angle is covered.
"""
from __future__ import annotations

import json
from pathlib import Path

from credit_workbench.normalize import eligibility

from . import fetch

OUT = Path(__file__).resolve().parents[1] / "universe.json"

# Issuers with a Hong Kong (primary or secondary) listing alongside their US ADS.
HK_DUAL_LISTED = {
    "BABA": "9988", "JD": "9618", "BIDU": "9888", "NTES": "9999", "TCOM": "9961",
    "BEKE": "2423", "LI": "2015", "NIO": "9866", "XPEV": "9868", "ZTO": "2057",
    "YUMC": "9987", "BILI": "9626", "TME": "1698", "WB": "9898", "HTHT": "1179",
    "BZ": "2076", "EDU": "9901", "MNSO": "9896", "GDS": "9698", "ZLAB": "9688",
    "KC": "3896", "ONC": "6160",
}
ANNUAL = {"10-K", "20-F", "40-F"}


def has_annual_xbrl_history(sub: dict) -> bool:
    forms = sub.get("filings", {}).get("recent", {}).get("form", [])
    return any(f in ANNUAL for f in forms)


def select(candidates: int = 720, target: int = 480) -> list[dict]:
    index = fetch.ticker_index()
    fields = index["fields"]
    rows = [dict(zip(fields, r)) for r in index["data"]]
    seen, picked = set(), []
    for rank, row in enumerate(rows):
        if row["exchange"] not in {"NYSE", "Nasdaq"}:
            continue
        cik = str(row["cik"]).zfill(10)
        if cik in seen:
            continue
        if len(picked) < candidates or row["ticker"] in HK_DUAL_LISTED:
            seen.add(cik)
            picked.append({**row, "cik": cik, "mcap_rank": rank + 1})
    print(f"candidates: {len(picked)}; fetching submissions…", flush=True)
    fetch.bulk([p["cik"] for p in picked], kinds=("submissions",))
    universe = []
    for p in picked:
        sub = fetch.submissions(p["cik"])
        if not sub:
            continue
        ok, reason = eligibility(sub)
        if not ok or not has_annual_xbrl_history(sub):
            continue
        hk = HK_DUAL_LISTED.get(p["ticker"])
        if len([u for u in universe if not u["hk"]]) >= target and not hk:
            continue
        universe.append({
            "ticker": p["ticker"], "cik": p["cik"], "name": sub.get("name") or p["name"],
            "exchange": p["exchange"], "sic": sub.get("sic"), "sic_description": sub.get("sicDescription"),
            "state": sub.get("stateOfIncorporation"), "fiscal_year_end": sub.get("fiscalYearEnd"),
            "category": sub.get("category"), "hk": hk, "mcap_rank": p["mcap_rank"],
        })
    OUT.write_text(json.dumps(universe, indent=1))
    print(f"universe: {len(universe)} issuers ({sum(1 for u in universe if u['hk'])} HK dual-listed) -> {OUT}")
    return universe


if __name__ == "__main__":
    select()
