"""SEC transport and dynamic issuer search. Financial normalization is separate."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

_RATE_LOCK = threading.Lock()
_NEXT_REQUEST = 0.0
_MAX_BYTES = 25 * 1024 * 1024


class SECError(RuntimeError):
    pass


def search_index(index: dict, query: str, limit: int = 20) -> list[dict]:
    """Search the live SEC ticker index, without a preset company allowlist."""
    query = query.strip()
    if not query or len(query) > 100 or not 1 <= limit <= 100:
        raise ValueError("Enter a company name/ticker (1–100 characters)")
    ticker_query = query.upper().replace(".", "-")
    words = query.casefold().split()
    matches = []
    for row in index.values():
        ticker = row["ticker"].upper()
        name = row["title"]
        normalized = ticker.replace(".", "-")
        rank = (0 if normalized == ticker_query else
                1 if normalized.startswith(ticker_query) else
                2 if all(w in name.casefold() for w in words) else None)
        if rank is not None:
            matches.append((rank, ticker, {"ticker": ticker, "name": name,
                                          "cik": str(row["cik_str"]).zfill(10)}))
    return [r[2] for r in sorted(matches, key=lambda r: (r[0], r[1]))[:limit]]


class SECClient:
    def __init__(self, identity: str, cache_dir: Path | str = ".cache/sec", timeout: float = 20):
        if (not re.search(r"[^\s@]+@[^\s@]+\.[^\s@]+", identity)
                or "example.com" in identity or "\n" in identity or "\r" in identity):
            raise ValueError("Set SEC_USER_AGENT to an app name and real operator contact email")
        self.identity = identity
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.statuses: dict[str, dict] = {}

    def _status(self, url: str, path: Path, *, stale: bool, reason: str = "") -> None:
        self.statuses[url] = {"stale": stale, "reason": reason,
                              "data_checked_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                              "last_attempt_at": datetime.now(timezone.utc).isoformat()}

    def _stale(self, url: str, path: Path, reason: str) -> dict | None:
        try:
            payload = json.loads(path.read_text())
            if isinstance(payload, dict):
                self._status(url, path, stale=True, reason=reason)
                return payload
        except (OSError, ValueError):
            pass
        return None

    def _get(self, url: str, ttl: int) -> dict:
        if urlparse(url).hostname not in {"www.sec.gov", "data.sec.gov"}:
            raise ValueError("Only SEC data endpoints are supported")
        path = self.cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".json")
        try:
            if time.time() - path.stat().st_mtime <= ttl:
                payload = json.loads(path.read_text())
                if isinstance(payload, dict):
                    self._status(url, path, stale=False)
                    return payload
        except (OSError, ValueError):
            pass
        for attempt in range(3):
            global _NEXT_REQUEST
            with _RATE_LOCK:
                time.sleep(max(0, _NEXT_REQUEST - time.monotonic()))
                _NEXT_REQUEST = time.monotonic() + 0.5  # 2/sec, plus EdgarTools' separate 2/sec budget
            request = Request(url, headers={"User-Agent": self.identity, "Accept": "application/json"})
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    body = response.read(_MAX_BYTES + 1)
                if len(body) > _MAX_BYTES:
                    raise SECError("SEC response exceeds the bounded download size")
                payload = json.loads(body)
                if not isinstance(payload, dict):
                    raise SECError("SEC returned an unexpected JSON schema")
                temp = path.with_suffix(f".{uuid4().hex}.tmp")
                try:
                    temp.write_bytes(body)
                    os.replace(temp, path)
                finally:
                    temp.unlink(missing_ok=True)
                self._status(url, path, stale=False)
                return payload
            except HTTPError as exc:
                if exc.code in {429, 500, 502, 503, 504} and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                reason = f"SEC HTTP {exc.code}; showing the last valid cached data."
                stale = self._stale(url, path, reason)
                if stale is not None:
                    return stale
                raise SECError(f"SEC HTTP {exc.code}. No valid cached response is available.") from None
            except (URLError, TimeoutError, ValueError, OSError):
                stale = self._stale(url, path, "SEC unavailable; showing the last valid cached data.")
                if stale is not None:
                    return stale
                raise SECError("SEC unavailable or invalid response; no substitute data was generated.") from None
        raise SECError("SEC retry limit reached")

    @staticmethod
    def _cik(cik: str) -> str:
        if not cik.isdigit() or not 1 <= len(cik) <= 10:
            raise ValueError("CIK must contain 1–10 digits")
        return cik.zfill(10)

    def search(self, query: str) -> list[dict]:
        index = self._get("https://www.sec.gov/files/company_tickers.json", 86400)
        return search_index(index, query)

    def submissions(self, cik: str, refresh: bool = False) -> dict:
        return self._get(f"https://data.sec.gov/submissions/CIK{self._cik(cik)}.json", 0 if refresh else 900)

    def company_facts(self, cik: str, refresh: bool = False) -> dict:
        return self._get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self._cik(cik)}.json", 0 if refresh else 900)

    def filing_html(self, url: str) -> str:
        parsed = urlparse(url)
        if (parsed.scheme != "https" or parsed.hostname != "www.sec.gov" or
                not parsed.path.startswith("/Archives/edgar/data/")):
            raise ValueError("Only SEC filing archive documents are supported")
        path = self.cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".html")
        try:
            if time.time() - path.stat().st_mtime <= 86400:
                return path.read_text(errors="replace")
        except OSError:
            pass
        global _NEXT_REQUEST
        with _RATE_LOCK:
            time.sleep(max(0, _NEXT_REQUEST - time.monotonic()))
            _NEXT_REQUEST = time.monotonic() + 0.5
        request = Request(url, headers={"User-Agent": self.identity, "Accept": "text/html"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read(_MAX_BYTES + 1)
            if len(body) > _MAX_BYTES:
                raise SECError("SEC filing exceeds the bounded download size")
            temp = path.with_suffix(f".{uuid4().hex}.tmp")
            try:
                temp.write_bytes(body)
                os.replace(temp, path)
            finally:
                temp.unlink(missing_ok=True)
            return body.decode("utf-8", errors="replace")
        except HTTPError as exc:
            raise SECError(f"SEC filing HTTP {exc.code}; disclosure extraction is unavailable.") from None
        except (URLError, TimeoutError, OSError):
            raise SECError("SEC filing unavailable; no disclosure passage was generated.") from None
