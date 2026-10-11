"""AI stage: cited filing passages + DeepSeek credit memo (English + Traditional Chinese).

Numbers never come from the model: memo text is digit-free by validation and the
UI shows figures from the deterministic tables. Each claim cites filing passages
and/or the SEC facts behind referenced metrics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from credit_workbench.disclosures import annual_document, extract_passages
from credit_workbench.memo import SECTIONS, MemoError, generate
from credit_workbench.memo_context import analyst_context as context_from_doc
from credit_workbench.normalize import normalize

from . import fetch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "public" / "data" / "ai"
MODEL = os.environ.get("DEEPSEEK_MODEL") or "deepseek-flash"
ZH_PROMPT_VERSION = "memo-zh-v1"


def _evidence_ref(evidence_id: str, passage_ids: dict[str, str]) -> dict:
    if evidence_id in passage_ids:
        return {"passage": passage_ids[evidence_id]}
    # cik:accession:concept:start|instant:end:currency:context  (concept may contain ':')
    parts = evidence_id.split(":")
    return {"accession": parts[1], "concept": ":".join(parts[2:-4])}


def translate(memo_payload: dict, api_key: str) -> dict:
    """Translate validated English claims into Traditional Chinese (HK financial usage)."""
    src = {s: [c["text"] for c in memo_payload[s]] for s in SECTIONS}
    system = ("You translate credit research into Traditional Chinese (繁體中文) as used by Hong Kong "
              "banks and rating agencies. Keep meaning exact; do not add or remove claims; do not add "
              "numbers or Arabic digits. Keep standard English financial abbreviations such as EBITDA, "
              "CFO, FCF where natural. Return only JSON with the same keys, each a list of strings in "
              "the same order and count.")
    for attempt in range(3):
        r = requests.post("https://api.deepseek.com/chat/completions",
                          headers={"Authorization": f"Bearer {api_key}"},
                          json={"model": MODEL, "response_format": {"type": "json_object"},
                                "thinking": {"type": "disabled"}, "temperature": 0.1, "max_tokens": 6000,
                                "messages": [{"role": "system", "content": system},
                                             {"role": "user", "content": json.dumps(src, ensure_ascii=False)}]},
                          timeout=(10, 120))
        r.raise_for_status()
        try:
            out = json.loads(r.json()["choices"][0]["message"]["content"])
        except ValueError:
            time.sleep(1 + attempt)
            continue
        if set(out) == set(SECTIONS) and all(len(out[s]) == len(src[s]) for s in SECTIONS) and \
                not any(re.search(r"[0-9]", t) for s in SECTIONS for t in out[s]):
            return out
        time.sleep(1 + attempt)
    raise MemoError("Chinese translation failed validation")


def analyst_context(t: str) -> dict:
    path = ROOT / "public" / "data" / "issuers" / f"{t}.json"
    return context_from_doc(json.loads(path.read_text())) if path.exists() else {}


def fingerprint(t: str) -> str | None:
    """Identity of the inputs a memo was written from: latest annual filing + primary-period facts."""
    path = ROOT / "public" / "data" / "issuers" / f"{t}.json"
    if not path.exists():
        return None
    d = json.loads(path.read_text())
    payload = json.dumps([d["filings"]["annual"], {k: v["value"] for k, v in d["facts"][d["primary"]].items()}],
                         sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def run_one(meta: dict, api_key: str, force: bool = False) -> str:
    t = meta["ticker"]
    path = OUT / f"{t}.json"
    fp = fingerprint(t)
    if path.exists() and not force:
        cached = json.loads(path.read_text())
        if cached.get("fingerprint") is None and fp:
            cached["fingerprint"] = fp  # adopt memos generated before fingerprints existed
            path.write_text(json.dumps(cached, ensure_ascii=False, separators=(",", ":")))
        if cached.get("fingerprint") not in (None, fp):
            return run_one(meta, api_key, force=True)
        if cached.get("memo", {}).get("zh"):
            return f"{t}: cached"
        en = cached["memo"]["en"]
        try:
            zh_text = translate({s: [{"text": c["text"]} for c in en[s]] for s in SECTIONS}, api_key)
        except Exception as exc:  # noqa: BLE001
            return f"{t}: zh retry failed ({exc})"
        cached["memo"]["zh"] = {s: [{**c, "text": zh_text[s][i]} for i, c in enumerate(en[s])] for s in SECTIONS}
        path.write_text(json.dumps(cached, ensure_ascii=False, separators=(",", ":")))
        return f"{t}: zh added"
    sub = fetch.submissions(meta["cik"])
    facts = fetch.companyfacts(meta["cik"])
    research = normalize(sub, facts, t, date.today())
    doc = annual_document(sub)
    if not doc:
        return f"{t}: no annual document"
    url, accession = doc
    html = fetch.cached_text("filings", accession, url)
    if not html:
        return f"{t}: filing unavailable"
    passages = extract_passages(html, url, accession)
    if not passages:
        return f"{t}: no extractable passages"
    pid = {p.evidence_id: f"P{i}" for i, p in enumerate(passages, 1)}
    snapshot = research.annual[0]
    last = None
    for attempt in range(3):
        try:
            memo = generate(snapshot, passages, api_key=api_key, model=MODEL, context=analyst_context(t))
            break
        except MemoError as exc:
            last = exc
            time.sleep(2)
    else:
        return f"{t}: memo failed ({last})"
    en = {s: [{"text": c.text, "evidence": [_evidence_ref(e, pid) for e in c.evidence_ids],
               "metrics": [m.replace("metric:", "") for m in c.metric_ids]} for c in memo.sections[s]]
          for s in SECTIONS}
    try:
        zh_text = translate({s: [{"text": c["text"]} for c in en[s]] for s in SECTIONS}, api_key)
        zh = {s: [{**c, "text": zh_text[s][i]} for i, c in enumerate(en[s])] for s in SECTIONS}
    except Exception as exc:  # noqa: BLE001
        zh = None
        print(f"  {t}: zh translation skipped ({exc})")
    payload = {
        "fingerprint": fp,
        "passages": [{"id": pid[p.evidence_id], "heading": p.heading, "text": p.text, "url": p.url,
                      "accession": p.accession} for p in passages],
        "memo": {"en": en, "zh": zh, "model": memo.model, "prompt_version": memo.prompt_version,
                 "generated_at": memo.generated_at, "period": snapshot.flow_period.end.isoformat(),
                 "status": "draft", "usage": {"input": memo.input_tokens, "output": memo.output_tokens}},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return f"{t}: ok ({memo.input_tokens}/{memo.output_tokens} tokens)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--stale-before", type=float, default=0,
                    help="with --force: only regenerate memo files last written before this unix time")
    args = ap.parse_args()
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is not set")
    universe = json.loads((Path(__file__).resolve().parents[1] / "universe.json").read_text())
    built = {p.stem for p in (ROOT / "public" / "data" / "issuers").glob("*.json")}
    only = {x.strip().upper() for x in args.only.split(",") if x.strip()}
    todo = [m for m in universe if (not only or m["ticker"] in only) and m["ticker"] in built]
    if args.limit:
        todo = todo[: args.limit]
    if args.force and args.stale_before:
        todo = [m for m in todo if not (OUT / f"{m['ticker']}.json").exists()
                or (OUT / f"{m['ticker']}.json").stat().st_mtime < args.stale_before]
    print(f"AI stage for {len(todo)} issuers with {MODEL}", flush=True)
    with ThreadPoolExecutor(args.workers) as pool:
        futs = {pool.submit(run_one, m, api_key, args.force): m["ticker"] for m in todo}
        for f in as_completed(futs):
            try:
                print(f.result(), flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"{futs[f]}: error {str(exc)[:200]}", flush=True)
    print("AI DONE", datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    main()
