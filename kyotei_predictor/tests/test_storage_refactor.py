#!/usr/bin/env python3
"""
storage (import_raw_to_db, delete_raw_after_import) の単体テスト。
"""
import tempfile
import json
from pathlib import Path
import pytest


class TestImportRawToDbFindPairs:
    """import_raw_to_db.find_pairs のテスト"""

    def test_empty_dir_returns_empty_list(self):
        from kyotei_predictor.tools.storage.import_raw_to_db import find_pairs
        with tempfile.TemporaryDirectory() as d:
            assert find_pairs(d) == []

    def test_nonexistent_dir_returns_empty_list(self):
        from kyotei_predictor.tools.storage.import_raw_to_db import find_pairs
        assert find_pairs("/nonexistent/path/raw") == []

    def test_pair_found_when_race_and_odds_match(self):
        from kyotei_predictor.tools.storage.import_raw_to_db import find_pairs
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "race_data_2025-01-15_KIRYU_R1.json").write_text("{}")
            (Path(d) / "odds_data_2025-01-15_KIRYU_R1.json").write_text("{}")
            pairs = find_pairs(d)
            assert len(pairs) == 1
            assert pairs[0][0] == "2025-01-15"
            assert pairs[0][1] == "KIRYU"
            assert pairs[0][2] == 1

    def test_subdir_rglob_finds_pairs(self):
        from kyotei_predictor.tools.storage.import_raw_to_db import find_pairs
        with tempfile.TemporaryDirectory() as d:
            sub = Path(d) / "2025-01"
            sub.mkdir()
            (sub / "race_data_2025-01-15_TODA_R2.json").write_text("{}")
            (sub / "odds_data_2025-01-15_TODA_R2.json").write_text("{}")
            pairs = find_pairs(d)
            assert len(pairs) == 1
            assert pairs[0][1] == "TODA" and pairs[0][2] == 2


class TestDeleteRawAfterImportFindPairs:
    """delete_raw_after_import.find_pairs のテスト"""

    def test_empty_dir_returns_empty_list(self):
        from kyotei_predictor.tools.storage.delete_raw_after_import import find_pairs
        with tempfile.TemporaryDirectory() as d:
            assert find_pairs(d) == []

    def test_pair_found_when_race_and_odds_match(self):
        from kyotei_predictor.tools.storage.delete_raw_after_import import find_pairs
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "race_data_2025-01-15_KIRYU_R1.json").write_text("{}")
            (Path(d) / "odds_data_2025-01-15_KIRYU_R1.json").write_text("{}")
            pairs = find_pairs(d)
            assert len(pairs) == 1
            assert len(pairs[0]) == 5  # (date, stadium, num, race_path, odds_path)
