"""Find stored memos that contradict the deterministic figures, and merge regenerated ones.

    python -m pipeline.memo_repair list            # comma-separated tickers with conflicts
    python -m pipeline.memo_repair audit           # conflict counts per language
    python -m pipeline.memo_repair merge T1,T2     # copy ai/<T>.json memo+passages into issuers/<T>.json

`merge` touches only the memo and passages of the named issuers; every figure,
peer statistic and source in the issuer file is left exactly as built.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from credit_workbench.consistency import audit_memo

DATA = Path(__file__).resolve().parents[2] / "public" / "data"


def _load(path: Path):
    return json.loads(path.read_text())


def conflicts(ticker: str, data: Path = DATA) -> dict[str, int]:
    """Per-language conflict counts for one issuer's stored AI memo (empty if none)."""
    ai = data / "ai" / f"{ticker}.json"
    if not ai.exists():
        return {}
    memo = _load(ai).get("memo") or {}
    audit = audit_memo(_load(data / "issuers" / f"{ticker}.json"), memo)
    return {lang: a["conflicts"] for lang, a in audit.items() if a["conflicts"]}


def conflicted_tickers(data: Path = DATA) -> list[str]:
    return sorted(p.stem for p in (data / "ai").glob("*.json") if conflicts(p.stem, data))


def merge(tickers: list[str], data: Path = DATA) -> list[str]:
    merged = []
    for t in tickers:
        ai, issuer = data / "ai" / f"{t}.json", data / "issuers" / f"{t}.json"
        if not (ai.exists() and issuer.exists()):
            continue
        extra = _load(ai)
        extra.pop("fingerprint", None)
        doc = _load(issuer)
        doc.update({k: extra[k] for k in ("memo", "passages") if k in extra})
        issuer.write_text(json.dumps(doc, separators=(",", ":"), default=str))
        merged.append(t)
    return merged


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "audit"
    if cmd == "list":
        print(",".join(conflicted_tickers()))
    elif cmd == "audit":
        bad = {t: conflicts(t) for t in conflicted_tickers()}
        total = len(list((DATA / "ai").glob("*.json")))
        print(f"{len(bad)} of {total} stored memos contain deterministic conflicts")
        for lang in ("en", "zh"):
            print(f"  {lang}: {sum(1 for c in bad.values() if lang in c)} memos, {sum(c.get(lang, 0) for c in bad.values())} claims")
    elif cmd == "merge" and len(argv) > 1:
        done = merge([t.strip().upper() for t in argv[1].split(",") if t.strip()])
        print(f"merged memos for {len(done)} issuers")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
