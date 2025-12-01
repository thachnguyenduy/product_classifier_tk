"""SQLite utilities for storing inspection results."""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


class ProductDatabase:
    """Minimal SQLite abstraction for the products table."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    result TEXT,
                    confidence REAL
                )
                """
            )
            conn.commit()

    def insert_result(self, timestamp: str, result: str, confidence: float) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO products (timestamp, result, confidence) VALUES (?, ?, ?)",
                (timestamp, result, confidence),
            )
            conn.commit()

    def fetch_results(self, filter_result: Optional[str] = None) -> List[Tuple]:
        query = "SELECT id, timestamp, result, confidence FROM products"
        params: Sequence = ()
        if filter_result in {"GOOD", "BAD"}:
            query += " WHERE result = ?"
            params = (filter_result,)
        query += " ORDER BY id DESC"

        with self._connect() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def export_to_csv(self, csv_path: Path, filter_result: Optional[str] = None) -> None:
        rows = self.fetch_results(filter_result)
        csv_path = Path(csv_path)
        with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["ID", "Timestamp", "Result", "Confidence"])
            writer.writerows(rows)

