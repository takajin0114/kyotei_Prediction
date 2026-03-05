#!/usr/bin/env python3
"""
メイン処理（第1優先）: DataIntegration の単体テスト。

- 初期化
- _validate_race_data（正常・必須不足で ValueError）
- _extract_race_id_from_filename
- get_race_entries_summary
- get_race_data(source="file") をファイルありで実行
"""
import json
import pytest
from pathlib import Path


def _minimal_race_data_for_integration():
    """DataIntegration._validate_race_data が要求する最小のデータ"""
    return {
        "race_info": {
            "date": "2024-06-01",
            "stadium": "KIRYU",
            "race_number": 1,
            "title": "テストレース",
        },
        "race_entries": [
            {
                "pit_number": i,
                "racer": {"name": f"選手{i}", "current_rating": "B1"},
                "performance": {"rate_in_all_stadium": 5.0, "rate_in_event_going_stadium": 4.0},
                "boat": {"number": str(i)},
                "motor": {"number": str(i + 10)},
            }
            for i in range(1, 7)
        ],
    }


class TestDataIntegrationMain:
    """DataIntegration のメイン処理テスト"""

    def test_init(self):
        from kyotei_predictor.data_integration import DataIntegration
        di = DataIntegration()
        assert hasattr(di, "get_race_data")
        assert hasattr(di, "cache")
        assert hasattr(di, "sample_data_path")

    def test_validate_race_data_valid_passes(self):
        from kyotei_predictor.data_integration import DataIntegration
        di = DataIntegration()
        data = _minimal_race_data_for_integration()
        di._validate_race_data(data)

    def test_validate_race_data_missing_race_info_raises(self):
        from kyotei_predictor.data_integration import DataIntegration
        di = DataIntegration()
        data = _minimal_race_data_for_integration()
        del data["race_info"]
        with pytest.raises(ValueError) as exc:
            di._validate_race_data(data)
        assert "必須" in str(exc.value) or "race_info" in str(exc.value)

    def test_validate_race_data_empty_entries_raises(self):
        from kyotei_predictor.data_integration import DataIntegration
        di = DataIntegration()
        data = _minimal_race_data_for_integration()
        data["race_entries"] = []
        with pytest.raises(ValueError) as exc:
            di._validate_race_data(data)
        assert "出走表" in str(exc.value) or "不正" in str(exc.value)

    def test_extract_race_id_from_filename(self):
        from kyotei_predictor.data_integration import DataIntegration
        di = DataIntegration()
        assert di._extract_race_id_from_filename("race_data_2024-06-01_KIRYU_R1.json") == "2024-06-01_KIRYU_R1"
        assert di._extract_race_id_from_filename("race_data_20240601_TODA_R2.json") == "2024-06-01_TODA_R2"
        assert di._extract_race_id_from_filename("complete_race_data_20240615_KIRYU_R1.json") == "2024-06-15_KIRYU_R1"
        assert di._extract_race_id_from_filename("other.json") is None

    def test_get_race_entries_summary(self):
        from kyotei_predictor.data_integration import DataIntegration
        di = DataIntegration()
        data = _minimal_race_data_for_integration()
        summary = di.get_race_entries_summary(data)
        assert len(summary) == 6
        assert summary[0]["pit_number"] == 1
        assert "racer_name" in summary[0]
        assert "rating" in summary[0]
        assert "all_stadium_rate" in summary[0]
        assert "local_rate" in summary[0]

    def test_get_race_data_file_source_with_temp_file(self, tmp_path, monkeypatch):
        import os
        import kyotei_predictor.data_integration as mod
        from kyotei_predictor.data_integration import DataIntegration
        data = _minimal_race_data_for_integration()
        fake_module_dir = tmp_path / "fake_module"
        data_dir = fake_module_dir / "data"
        data_dir.mkdir(parents=True)
        race_file = data_dir / "race_data_2024-06-01_KIRYU_R1.json"
        race_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(mod, "__file__", str(fake_module_dir / "data_integration.py"))
        di = DataIntegration()
        out = di.get_race_data(source="file", race_id="2024-06-01_KIRYU_R1")
        assert out["race_info"]["stadium"] == "KIRYU"
        assert len(out["race_entries"]) == 6

    def test_get_race_data_invalid_source_raises(self):
        from kyotei_predictor.data_integration import DataIntegration
        di = DataIntegration()
        with pytest.raises(ValueError) as exc:
            di.get_race_data(source="invalid")
        assert "不正なデータソース" in str(exc.value)