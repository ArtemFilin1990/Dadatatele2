from __future__ import annotations

import sqlite3
from pathlib import Path


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS okved2 (code TEXT PRIMARY KEY, title TEXT);
        CREATE TABLE IF NOT EXISTS okopf (code TEXT PRIMARY KEY, title TEXT);
        CREATE TABLE IF NOT EXISTS okfs (code TEXT PRIMARY KEY, title TEXT);
        CREATE TABLE IF NOT EXISTS okpd (code TEXT PRIMARY KEY, title TEXT);
        CREATE TABLE IF NOT EXISTS okpd2 (code TEXT PRIMARY KEY, title TEXT);
        CREATE TABLE IF NOT EXISTS account_codes (code TEXT PRIMARY KEY, title TEXT);
        CREATE TABLE IF NOT EXISTS statuses (code TEXT PRIMARY KEY, title TEXT);
        """
    )


def build(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    build(Path("reference_data.db"))
    print("reference_data.db is ready")
