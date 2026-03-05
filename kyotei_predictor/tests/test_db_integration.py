#!/usr/bin/env python3
"""pipelines.db_integration (KyoteiDB) の単体テスト"""
import json
import tempfile
from pathlib import Path

import pytest


class TestKyoteiDB:
    def test_import(self):
        from kyotei_predictor.pipelines.db_integration import KyoteiDB
        assert KyoteiDB is not None

    def test_create_and_insert_race_and_fetch(self, tmp_path):
        from kyotei_predictor.pipelines.db_integration import KyoteiDB
        db_path = str(tmp_path / "test.db")
        db = KyoteiDB(db_path=db_path)
        db.insert_race({
            "race_id": "r1",
            "date": "2024-01-01",
            "stadium": "KIRYU",
            "round": 1,
            "weather": "晴",
            "wind_velocity": 2.5,
            "air_temperature": 15.0,
        })
        row = db.fetch_race("r1")
        assert row is not None
        assert row["race_id"] == "r1"
        assert row["stadium"] == "KIRYU"
        assert row["round"] == 1

    def test_insert_results_fetch_all_fetch_by_race_close(self, tmp_path):
        from kyotei_predictor.pipelines.db_integration import KyoteiDB
        db_path = str(tmp_path / "test.db")
        db = KyoteiDB(db_path=db_path)
        db.insert_race({"race_id": "r1", "date": "2024-01-01", "stadium": "KIRYU", "round": 1, "weather": "", "wind_velocity": None, "air_temperature": None})
        db.insert_results([
            {"race_id": "r1", "pit_number": 1, "arrival": 1, "start_time": 0.15, "total_time": 100.5},
            {"race_id": "r1", "pit_number": 2, "arrival": 2, "start_time": 0.12, "total_time": 101.0},
        ])
        all_races = db.fetch_all_races()
        assert len(all_races) == 1
        results = db.fetch_results_by_race("r1")
        assert len(results) == 2
        db.close()

    def test_import_race_json_and_bulk(self, tmp_path):
        from kyotei_predictor.pipelines.db_integration import KyoteiDB, import_race_json, import_race_json_bulk
        db_path = str(tmp_path / "test.db")
        db = KyoteiDB(db_path=db_path)
        race_file = tmp_path / "race_data_2024-01-01_KIRYU_R1.json"
        race_file.write_text(json.dumps({
            "race_info": {"date": "2024-01-01", "stadium": "KIRYU", "race_number": 1, "weather": "晴", "wind_velocity": 2.0, "air_temperature": 15.0},
            "race_records": [
                {"pit_number": 1, "arrival": 1, "start_time": 0.15, "total_time": 100.0},
                {"pit_number": 2, "arrival": 2, "start_time": 0.12, "total_time": 101.0},
            ],
        }, ensure_ascii=False), encoding="utf-8")
        import_race_json(str(race_file), db)
        row = db.fetch_race("2024-01-01_KIRYU_R1")
        assert row is not None
        import_race_json_bulk(str(tmp_path), db)
        db.close()
