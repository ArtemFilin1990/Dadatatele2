from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class SQLiteTTLCache:
    def __init__(self, db_path: Path, default_ttl: int) -> None:
        self.default_ttl = default_ttl
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_exp ON cache(expires_at)")
            conn.commit()

    async def get(self, key: str) -> Any | None:
        now = time.time()
        with self._connect() as conn:
            row = conn.execute("SELECT value_json, expires_at FROM cache WHERE key=?", (key,)).fetchone()
            if not row:
                return None
            value_json, expires_at = row
            if float(expires_at) <= now:
                conn.execute("DELETE FROM cache WHERE key=?", (key,))
                conn.commit()
                return None
            return json.loads(value_json)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + ttl_seconds
        value_json = json.dumps(value, ensure_ascii=False, default=str)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache(key, value_json, expires_at) VALUES(?,?,?)",
                (key, value_json, expires_at),
            )
            conn.commit()
