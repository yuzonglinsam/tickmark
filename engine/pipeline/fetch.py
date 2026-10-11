"""Bulk SEC downloader for the coverage universe.

Respects SEC fair-access guidance (declared User-Agent, <10 requests/second).
Raw responses are cached gzip-compressed under RAW_DIR so the pipeline can be
re-run offline. Nothing here interprets financial values.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

RAW_DIR = Path(os.environ.get("TICKMARK_RAW_DIR", Path(__file__).resolve().parents[2] / ".rawdata"))
RATE = 8.0  # requests per second, below SEC's 10/s ceiling

_lock = threading.Lock()
_next = 0.0
_session = requests.Session()


def _throttle() -> None:
    global _next
    with _lock:
        now = time.monotonic()
        wait = max(0.0, _next - now)
        _next = max(now, _next) + 1.0 / RATE
    if wait:
        time.sleep(wait)


def identity() -> str:
    ua = os.environ.get("SEC_USER_AGENT", "").strip().strip('"')
    if "@" not in ua:
        raise SystemExit("Set SEC_USER_AGENT (name + email) before fetching from SEC")
    return ua


def get(url: str, *, binary: bool = False, retries: int = 4):
    for attempt in range(retries):
        _throttle()
        try:
            r = _session.get(url, headers={"User-Agent": identity(), "Accept-Encoding": "gzip, deflate"},
                             timeout=60)
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 404:
            return None
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt + 1)
            continue
        r.raise_for_status()
        return r.content if binary else r.json()
    raise RuntimeError(f"SEC request failed after retries: {url}")


def cached_json(kind: str, key: str, url: str, max_age: float = 7 * 86400) -> dict | None:
    path = RAW_DIR / kind / f"{key}.json.gz"
    if path.exists() and time.time() - path.stat().st_mtime < max_age:
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    data = get(url)
    if data is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt") as fh:
        json.dump(data, fh)
    os.replace(tmp, path)
    return data


def cached_text(kind: str, key: str, url: str, max_age: float = 30 * 86400) -> str | None:
    path = RAW_DIR / kind / f"{key}.html.gz"
    if path.exists() and time.time() - path.stat().st_mtime < max_age:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    body = get(url, binary=True)
    if body is None:
        return None
    text = body.decode("utf-8", errors="replace")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)
    return text


def submissions(cik: str) -> dict | None:
    cik = str(cik).zfill(10)
    return cached_json("submissions", cik, f"https://data.sec.gov/submissions/CIK{cik}.json")


def companyfacts(cik: str) -> dict | None:
    cik = str(cik).zfill(10)
    return cached_json("companyfacts", cik, f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")


def ticker_index() -> dict:
    return cached_json("index", "company_tickers_exchange",
                       "https://www.sec.gov/files/company_tickers_exchange.json", max_age=86400)


def bulk(ciks: list[str], kinds=("submissions", "companyfacts"), workers: int = 6) -> dict:
    fn = {"submissions": submissions, "companyfacts": companyfacts}
    results = {}
    with ThreadPoolExecutor(workers) as pool:
        futures = {pool.submit(fn[k], c): (k, c) for c in ciks for k in kinds}
        for i, fut in enumerate(as_completed(futures), 1):
            k, c = futures[fut]
            try:
                results[(k, c)] = fut.result() is not None
            except Exception as exc:  # noqa: BLE001 - report and continue
                results[(k, c)] = False
                print(f"  ! {k} {c}: {exc}")
            if i % 100 == 0:
                print(f"  fetched {i}/{len(futures)}", flush=True)
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ciks", nargs="*")
    args = ap.parse_args()
    print(bulk(args.ciks))
