from __future__ import annotations

import sqlite3
from pathlib import Path


class ReferenceDataService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _lookup(self, table: str, code: str) -> str:
        if not code or not self.db_path.exists():
            return "расшифровка не найдена"
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(f"SELECT title FROM {table} WHERE code=?", (code,)).fetchone()
            return row[0] if row else "расшифровка не найдена"

    def okved_name(self, code: str) -> str:
        return self._lookup("okved2", code)

    def okopf_name(self, code: str) -> str:
        return self._lookup("okopf", code)

    def okfs_name(self, code: str) -> str:
        return self._lookup("okfs", code)

    def okpd_name(self, code: str) -> str:
        return self._lookup("okpd", code)

    def account_code_name(self, code: str) -> str:
        return self._lookup("account_codes", code)

    def status_name(self, code: str) -> str:
        return self._lookup("statuses", code)
