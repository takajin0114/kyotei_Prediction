"""
学習用レース・オッズデータの SQLite 保管モジュール。

スキーマ:
- races: (race_date, stadium, race_number) を主キーに、race_data の全文を race_json (TEXT) で保持
- odds: 同上、odds_data の全文を odds_json (TEXT) で保持
- race_canceled: 中止レースの (race_date, stadium, race_number) のみ記録（学習では除外）

学習パイプラインは race_json / odds_json を JSON として復元し、既存の build_race_state_vector 等に渡す。
"""
from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "kyotei_races.sqlite")


def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


class RaceDB:
    """学習用レース・オッズを SQLite で扱う。"""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)) or ".", exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = _dict_factory
        return self._conn

    def create_tables(self) -> None:
        """テーブルが無ければ作成する。"""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS races (
                race_date TEXT NOT NULL,
                stadium TEXT NOT NULL,
                race_number INTEGER NOT NULL,
                race_json TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (race_date, stadium, race_number)
            );
            CREATE INDEX IF NOT EXISTS idx_races_date ON races(race_date);
            CREATE INDEX IF NOT EXISTS idx_races_stadium ON races(stadium);

            CREATE TABLE IF NOT EXISTS odds (
                race_date TEXT NOT NULL,
                stadium TEXT NOT NULL,
                race_number INTEGER NOT NULL,
                odds_json TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (race_date, stadium, race_number)
            );
            CREATE INDEX IF NOT EXISTS idx_odds_date ON odds(race_date);

            CREATE TABLE IF NOT EXISTS race_canceled (
                race_date TEXT NOT NULL,
                stadium TEXT NOT NULL,
                race_number INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (race_date, stadium, race_number)
            );
        """)
        conn.commit()

    def insert_race(self, race_date: str, stadium: str, race_number: int, race_data: Dict[str, Any]) -> None:
        """レース 1 件を挿入（既存は上書き）。"""
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO races (race_date, stadium, race_number, race_json) VALUES (?, ?, ?, ?)",
            (race_date, stadium, race_number, json.dumps(race_data, ensure_ascii=False)),
        )
        conn.commit()

    def insert_odds(self, race_date: str, stadium: str, race_number: int, odds_data: Dict[str, Any]) -> None:
        """オッズ 1 件を挿入（既存は上書き）。"""
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO odds (race_date, stadium, race_number, odds_json) VALUES (?, ?, ?, ?)",
            (race_date, stadium, race_number, json.dumps(odds_data, ensure_ascii=False)),
        )
        conn.commit()

    def insert_race_canceled(self, race_date: str, stadium: str, race_number: int) -> None:
        """中止レース 1 件を記録。"""
        conn = self._get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO race_canceled (race_date, stadium, race_number) VALUES (?, ?, ?)",
            (race_date, stadium, race_number),
        )
        conn.commit()

    def get_race_json(self, race_date: str, stadium: str, race_number: int) -> Optional[Dict[str, Any]]:
        """1 レース分の race_data 辞書を取得。無ければ None。"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT race_json FROM races WHERE race_date = ? AND stadium = ? AND race_number = ?",
            (race_date, stadium, race_number),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["race_json"])

    def get_odds_json(self, race_date: str, stadium: str, race_number: int) -> Optional[Dict[str, Any]]:
        """1 レース分の odds_data 辞書を取得。無ければ None。"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT odds_json FROM odds WHERE race_date = ? AND stadium = ? AND race_number = ?",
            (race_date, stadium, race_number),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["odds_json"])

    def get_race_odds_pairs(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        year_month: Optional[str] = None,
        stadium: Optional[str] = None,
    ) -> List[Tuple[str, str, int]]:
        """
        race と odds の両方がある (race_date, stadium, race_number) の一覧を返す。
        学習で「ペアが揃ったレース」だけ使うために使う。
        year_month 指定時は race_date LIKE 'year_month%' で絞る（例: "2024-05"）。
        """
        conn = self._get_conn()
        q = """
            SELECT r.race_date, r.stadium, r.race_number
            FROM races r
            INNER JOIN odds o ON r.race_date = o.race_date AND r.stadium = o.stadium AND r.race_number = o.race_number
            WHERE 1=1
        """
        params: List[Any] = []
        if year_month:
            q += " AND r.race_date LIKE ?"
            params.append(f"{year_month}%")
        if date_from:
            q += " AND r.race_date >= ?"
            params.append(date_from)
        if date_to:
            q += " AND r.race_date <= ?"
            params.append(date_to)
        if stadium:
            q += " AND r.stadium = ?"
            params.append(stadium)
        q += " ORDER BY r.race_date, r.stadium, r.race_number"
        rows = conn.execute(q, params).fetchall()
        return [(r["race_date"], r["stadium"], r["race_number"]) for r in rows]

    def count_races(self) -> int:
        """races テーブルの件数。"""
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) AS n FROM races").fetchone()
        return row["n"] if row else 0

    def count_pairs(self) -> int:
        """race と odds のペア数。"""
        return len(self.get_race_odds_pairs())

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "RaceDB":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
