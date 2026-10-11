"""Build issuer JSON files + the universe index from cached SEC data.

Usage:  python -m pipeline.build [--only KO,PEP] [--out ../public/data]
"""
from __future__ import annotations

import argparse
import json
import statistics
import traceback
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from credit_workbench.export import build_issuer, summary_row

from . import fetch

ROOT = Path(__file__).resolve().parents[2]
UNIVERSE = Path(__file__).resolve().parents[1] / "universe.json"
PEER_KEYS = ("lev", "nlev", "icov", "ecov", "cfod", "fcfd", "om", "cr", "g", "z")
LOWER_IS_BETTER = {"lev", "nlev"}


def percentile_rank(values: list[float], x: float) -> float:
    below = sum(1 for v in values if v < x)
    equal = sum(1 for v in values if v == x)
    return (below + 0.5 * equal) / len(values)


def peers(rows: list[dict]) -> dict:
    by_sector = defaultdict(list)
    for r in rows:
        by_sector[r["s"]].append(r)
    stats = {}
    for sec, items in by_sector.items():
        stats[sec] = {"count": len(items)}
        for k in PEER_KEYS:
            vals = sorted(r[k] for r in items if r.get(k) is not None)
            if len(vals) >= 3:
                stats[sec][k] = {"median": statistics.median(vals), "p25": vals[len(vals) // 4],
                                 "p75": vals[(3 * len(vals)) // 4], "n": len(vals), "values": vals}
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default=str(ROOT / "public" / "data"))
    args = ap.parse_args()
    out = Path(args.out)
    (out / "issuers").mkdir(parents=True, exist_ok=True)
    universe = json.loads(UNIVERSE.read_text())
    only = {t.strip().upper() for t in args.only.split(",") if t.strip()}
    rows, failures, docs = [], [], {}
    today = date.today()
    for meta in universe:
        if only and meta["ticker"] not in only:
            continue
        try:
            sub = fetch.submissions(meta["cik"])
            facts = fetch.companyfacts(meta["cik"])
            if not sub or not facts:
                raise ValueError("SEC submissions/companyfacts unavailable")
            doc = build_issuer(meta, sub, facts, today)
            docs[meta["ticker"]] = doc
            rows.append(summary_row(doc))
        except Exception as exc:  # noqa: BLE001 - every failure is reported, none hidden
            failures.append({"ticker": meta["ticker"], "name": meta["name"], "reason": str(exc)[:300]})
            if only:
                traceback.print_exc()
    stats = peers(rows)
    for r in rows:
        sec_stats = stats.get(r["s"], {})
        pct = {}
        for k in PEER_KEYS:
            st = sec_stats.get(k)
            if st and r.get(k) is not None:
                p = percentile_rank(st["values"], r[k])
                pct[k] = 1 - p if k in LOWER_IS_BETTER else p
        docs[r["t"]]["peers"] = {"sector": r["s"], "count": sec_stats.get("count", 0), "percentile": pct,
                                 "median": {k: v["median"] for k, v in sec_stats.items() if isinstance(v, dict)}}
    # merge memo/passages produced by the AI stage, if present
    for t, doc in docs.items():
        ai = out / "ai" / f"{t}.json"
        if ai.exists():
            extra = json.loads(ai.read_text())
            extra.pop("fingerprint", None)
            doc.update(extra)
        (out / "issuers" / f"{t}.json").write_text(json.dumps(doc, separators=(",", ":"), default=str))
    for sec_stats in stats.values():
        for v in sec_stats.values():
            if isinstance(v, dict):
                v.pop("values", None)
    for r in rows:
        r["memo"] = bool(docs[r["t"]].get("memo"))
    index = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "count": len(rows), "issuers": rows, "sectors": stats,
             "excluded": failures}
    if not only:
        (out / "universe.json").write_text(json.dumps(index, separators=(",", ":"), default=str))
        idx = fetch.ticker_index()
        seen, tickers = set(), []
        for r in idx["data"]:
            row = dict(zip(idx["fields"], r))
            if row["ticker"] in seen:
                continue
            seen.add(row["ticker"])
            tickers.append([row["ticker"], row["name"], row["cik"]])
        (out / "tickers.json").write_text(json.dumps(tickers, separators=(",", ":")))
    print(f"built {len(rows)} issuers, {len(failures)} excluded")
    for f in failures[:60]:
        print("  -", f["ticker"], ":", f["reason"][:140])


if __name__ == "__main__":
    main()
