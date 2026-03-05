#!/usr/bin/env python3
"""
race_db の単体テスト（DB スキーマ・投入・取得）。
"""
import tempfile
import json
import pytest
from pathlib import Path


class TestRaceDB:
    """RaceDB のテスト"""

    def test_create_tables_and_count_empty(self):
        """テーブル作成後、空の DB で count が 0"""
        from kyotei_predictor.data.race_db import RaceDB
        with tempfile.TemporaryDirectory() as d:
            db_path = str(Path(d) / "test.sqlite")
            db = RaceDB(db_path)
            db.create_tables()
            assert db.count_races() == 0
            assert db.count_pairs() == 0
            db.close()

    def test_insert_race_and_get(self):
        """1件投入して get_race_json で取得"""
        from kyotei_predictor.data.race_db import RaceDB
        with tempfile.TemporaryDirectory() as d:
            db_path = str(Path(d) / "test.sqlite")
            db = RaceDB(db_path)
            db.create_tables()
            db.insert_race("2025-01-15", "KIRYU", 1, {"title": "test"})
            out = db.get_race_json("2025-01-15", "KIRYU", 1)
            assert out is not None
            assert out.get("title") == "test"
            db.close()

    def test_get_race_odds_pairs_returns_matching_pairs(self):
        """race と odds の両方がある場合のみペアに含まれる"""
        from kyotei_predictor.data.race_db import RaceDB
        with tempfile.TemporaryDirectory() as d:
            db_path = str(Path(d) / "test.sqlite")
            db = RaceDB(db_path)
            db.create_tables()
            db.insert_race("2025-01-15", "KIRYU", 1, {})
            assert db.count_pairs() == 0
            db.insert_odds("2025-01-15", "KIRYU", 1, {})
            assert db.count_pairs() == 1
            pairs = db.get_race_odds_pairs()
            assert len(pairs) == 1
            assert pairs[0] == ("2025-01-15", "KIRYU", 1)
            db.close()

    def test_insert_race_canceled_and_get_odds_json(self):
        from kyotei_predictor.data.race_db import RaceDB
        with tempfile.TemporaryDirectory() as d:
            db_path = str(Path(d) / "test.sqlite")
            db = RaceDB(db_path)
            db.create_tables()
            db.insert_race("2025-01-15", "KIRYU", 1, {"a": 1})
            db.insert_odds("2025-01-15", "KIRYU", 1, {"odds": 10.5})
            assert db.get_odds_json("2025-01-15", "KIRYU", 1) == {"odds": 10.5}
            assert db.get_odds_json("2025-01-15", "KIRYU", 2) is None
            assert db.get_race_json("2025-01-15", "KIRYU", 2) is None
            db.insert_race_canceled("2025-01-16", "TODA", 3)
            db.close()

    def test_get_race_odds_pairs_with_filters(self):
        from kyotei_predictor.data.race_db import RaceDB
        with tempfile.TemporaryDirectory() as d:
            db_path = str(Path(d) / "test.sqlite")
            db = RaceDB(db_path)
            db.create_tables()
            db.insert_race("2025-01-10", "KIRYU", 1, {})
            db.insert_odds("2025-01-10", "KIRYU", 1, {})
            db.insert_race("2025-01-15", "KIRYU", 1, {})
            db.insert_odds("2025-01-15", "KIRYU", 1, {})
            db.insert_race("2025-01-20", "TODA", 1, {})
            db.insert_odds("2025-01-20", "TODA", 1, {})
            pairs = db.get_race_odds_pairs(year_month="2025-01")
            assert len(pairs) == 3
            pairs = db.get_race_odds_pairs(date_from="2025-01-12", date_to="2025-01-18")
            assert len(pairs) == 1
            assert pairs[0] == ("2025-01-15", "KIRYU", 1)
            pairs = db.get_race_odds_pairs(stadium="TODA")
            assert len(pairs) == 1
            assert db.count_pairs() == 3
            db.close()

    def test_context_manager(self):
        from kyotei_predictor.data.race_db import RaceDB
        with tempfile.TemporaryDirectory() as d:
            db_path = str(Path(d) / "test.sqlite")
            with RaceDB(db_path) as db:
                db.create_tables()
                assert db.count_races() == 0
            db2 = RaceDB(db_path)
            db2._get_conn()
            db2.close()
            assert db2._conn is None
