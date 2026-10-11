"""Shared memo persistence and duplicate paid-request prevention."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
import json
import sqlite3
import time
from pathlib import Path

from .memo import Claim, Memo


class MemoStore:
    def __init__(self, database_url: str | None = None, local_path: str = ".cache/memos.sqlite"):
        self.database_url = database_url or None
        self.local_path = local_path
        if not self.database_url:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS memos ("
                               "cache_key TEXT PRIMARY KEY, state TEXT NOT NULL, "
                               "payload TEXT, started_at DOUBLE PRECISION NOT NULL)")
            connection.execute("CREATE TABLE IF NOT EXISTS api_calls ("
                               "requested_at DOUBLE PRECISION NOT NULL)")
            connection.execute("CREATE TABLE IF NOT EXISTS analyses ("
                               "cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL, saved_at DOUBLE PRECISION NOT NULL)")

    @property
    def durable(self) -> bool:
        return bool(self.database_url)

    @contextmanager
    def _connection(self):
        if self.database_url:
            import psycopg
            connection = psycopg.connect(self.database_url, connect_timeout=5)
        else:
            connection = sqlite3.connect(self.local_path, timeout=10)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _sql(self, text: str) -> str:
        return text.replace("?", "%s") if self.database_url else text

    @staticmethod
    def _decode(payload: str) -> Memo:
        data = json.loads(payload)
        data["sections"] = {key: tuple(Claim(claim['text'], tuple(claim['evidence_ids']), tuple(claim['metric_ids'])) for claim in claims)
                            for key, claims in data["sections"].items()}
        return Memo(**data)

    def save_analysis(self, key: str, payload: dict) -> None:
        encoded = json.dumps(payload, ensure_ascii=False)
        if len(encoded) > 2_000_000:
            raise ValueError("Public analysis exceeds storage limit")
        with self._connection() as connection:
            connection.execute(self._sql("INSERT INTO analyses(cache_key,payload,saved_at) VALUES(?,?,?) "
                               "ON CONFLICT(cache_key) DO UPDATE SET payload=excluded.payload,saved_at=excluded.saved_at"),
                               (key, encoded, time.time()))

    def get_analysis(self, key: str, max_age: float | None = None) -> dict | None:
        with self._connection() as connection:
            row = connection.execute(self._sql("SELECT payload,saved_at FROM analyses WHERE cache_key=?"), (key,)).fetchone()
        if row and max_age is not None and time.time() - row[1] > max_age:
            return None
        return json.loads(row[0]) if row else None

    def get(self, key: str) -> Memo | None:
        with self._connection() as connection:
            row = connection.execute(self._sql("SELECT payload FROM memos WHERE cache_key=? AND state='ready'"),
                                     (key,)).fetchone()
        return self._decode(row[0]) if row else None

    def claim(self, key: str) -> bool:
        """Atomically claim a memo key; stale in-flight leases expire after 3 minutes."""
        now = time.time()
        with self._connection() as connection:
            if not self.database_url:
                connection.execute("BEGIN IMMEDIATE")
            statement = self._sql("INSERT INTO memos(cache_key,state,payload,started_at) "
                                  "VALUES(?,'generating',NULL,?) ON CONFLICT(cache_key) DO NOTHING")
            cursor = connection.execute(statement, (key, now))
            if cursor.rowcount == 1:
                return True
            row = connection.execute(self._sql("SELECT state,started_at FROM memos WHERE cache_key=?"),
                                     (key,)).fetchone()
            if row and row[0] == "generating" and now - row[1] > 180:
                cursor = connection.execute(self._sql(
                    "UPDATE memos SET started_at=? WHERE cache_key=? AND state='generating' AND started_at=?"),
                    (now, key, row[1]))
                return cursor.rowcount == 1
            return False

    def finish(self, key: str, memo: Memo) -> None:
        payload = json.dumps(asdict(memo), ensure_ascii=False)
        with self._connection() as connection:
            connection.execute(self._sql("UPDATE memos SET state='ready',payload=? WHERE cache_key=?"),
                               (payload, key))

    def release(self, key: str) -> None:
        with self._connection() as connection:
            connection.execute(self._sql("DELETE FROM memos WHERE cache_key=? AND state='generating'"),
                               (key,))

    def wait(self, key: str, seconds: int = 55) -> Memo | None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            result = self.get(key)
            if result:
                return result
            time.sleep(2)
        return None

    def allow_call(self, limit_per_hour: int = 30, max_concurrency: int = 2) -> bool:
        """Rolling shared limit, distinct from the user's per-session cooldown."""
        now = time.time()
        with self._connection() as connection:
            if self.database_url:
                connection.execute("SELECT pg_advisory_xact_lock(947190)")
            else:
                connection.execute("BEGIN IMMEDIATE")
            active = connection.execute(self._sql("SELECT COUNT(*) FROM memos WHERE state='generating' AND started_at>?"),
                                        (now - 180,)).fetchone()[0]
            if active > max_concurrency:
                return False
            connection.execute(self._sql("DELETE FROM api_calls WHERE requested_at<?"), (now - 3600,))
            count = connection.execute("SELECT COUNT(*) FROM api_calls").fetchone()[0]
            if count >= limit_per_hour:
                return False
            connection.execute(self._sql("INSERT INTO api_calls(requested_at) VALUES(?)"), (now,))
            return True
