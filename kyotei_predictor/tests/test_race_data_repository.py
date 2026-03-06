"""
レースデータ repository（JSON / DB）と data_source 切替のテスト。

- JSON repository が従来通り動くこと
- DB repository が同等のレースデータを返すこと
- baseline_train が data_source=json / db の両方で動くこと
- 既存フローを壊していないこと
"""

import json
import tempfile
import pytest
from pathlib import Path


def _minimal_race_data_with_result(stadium: str = "KIRYU", race_number: int = 1):
    """着順入りの最小 race_data"""
    return {
        "race_info": {"stadium": stadium, "race_number": race_number, "number_of_laps": 3, "is_course_fixed": False},
        "race_records": [
            {"pit_number": i, "arrival": i} for i in range(1, 7)
        ],
        "race_entries": [
            {"pit_number": i, "racer": {"current_rating": "B1"}, "performance": {"rate_in_all_stadium": 5.0, "rate_in_event_going_stadium": 5.0}, "boat": {"quinella_rate": 50.0, "trio_rate": 50.0}, "motor": {"quinella_rate": 50.0, "trio_rate": 50.0}}
            for i in range(1, 7)
        ],
    }


class TestJsonRaceDataRepository:
    """JSON リポジトリのテスト（従来互換）"""

    def test_load_race(self, tmp_path):
        from kyotei_predictor.infrastructure.repositories.json_race_data_repository import JsonRaceDataRepository
        (tmp_path / "race_data_2024-06-01_KIRYU_R1.json").write_text(
            json.dumps(_minimal_race_data_with_result("KIRYU", 1), ensure_ascii=False)
        )
        repo = JsonRaceDataRepository(tmp_path)
        out = repo.load_race("2024-06-01", "KIRYU", 1)
        assert out is not None
        assert out.get("race_info", {}).get("stadium") == "KIRYU"
        assert out.get("race_records") and len(out["race_records"]) == 6

    def test_load_race_missing_returns_none(self, tmp_path):
        from kyotei_predictor.infrastructure.repositories.json_race_data_repository import JsonRaceDataRepository
        repo = JsonRaceDataRepository(tmp_path)
        assert repo.load_race("2024-06-01", "KIRYU", 1) is None

    def test_load_races_between(self, tmp_path):
        from kyotei_predictor.infrastructure.repositories.json_race_data_repository import JsonRaceDataRepository
        for i in range(3):
            (tmp_path / f"race_data_2024-06-0{i+1}_KIRYU_R1.json").write_text(
                json.dumps(_minimal_race_data_with_result(), ensure_ascii=False)
            )
        repo = JsonRaceDataRepository(tmp_path)
        races = repo.load_races_between("2024-06-01", "2024-06-03")
        assert len(races) == 3
        races_limited = repo.load_races_between("2024-06-01", "2024-06-10", max_samples=2)
        assert len(races_limited) == 2

    def test_load_races_by_date(self, tmp_path):
        from kyotei_predictor.infrastructure.repositories.json_race_data_repository import JsonRaceDataRepository
        (tmp_path / "race_data_2024-06-15_KIRYU_R1.json").write_text(json.dumps(_minimal_race_data_with_result("KIRYU", 1), ensure_ascii=False))
        (tmp_path / "race_data_2024-06-15_KIRYU_R2.json").write_text(json.dumps(_minimal_race_data_with_result("KIRYU", 2), ensure_ascii=False))
        repo = JsonRaceDataRepository(tmp_path)
        list_ = repo.load_races_by_date("2024-06-15")
        assert len(list_) == 2
        data, venue, rno = list_[0]
        assert venue in ("KIRYU",)
        assert rno in (1, 2)
        assert "race_records" in data


class TestDbRaceDataRepository:
    """DB リポジトリのテスト"""

    def test_load_race_and_races_between(self):
        from kyotei_predictor.data.race_db import RaceDB
        from kyotei_predictor.infrastructure.repositories.db_race_data_repository import DbRaceDataRepository
        with tempfile.TemporaryDirectory() as d:
            db_path = str(Path(d) / "test.sqlite")
            db = RaceDB(db_path)
            db.create_tables()
            for i in range(1, 4):
                db.insert_race("2024-07-01", "TODA", i, _minimal_race_data_with_result("TODA", i))
                db.insert_odds("2024-07-01", "TODA", i, {"trifecta": {}})
            db.close()

            repo = DbRaceDataRepository(db_path)
            out = repo.load_race("2024-07-01", "TODA", 1)
            assert out is not None
            assert out.get("race_info", {}).get("stadium") == "TODA"
            between = repo.load_races_between("2024-07-01", "2024-07-01")
            assert len(between) == 3
            by_date = repo.load_races_by_date("2024-07-01")
            assert len(by_date) == 3
            repo.close()

    def test_load_races_by_date_venues_filter(self):
        from kyotei_predictor.data.race_db import RaceDB
        from kyotei_predictor.infrastructure.repositories.db_race_data_repository import DbRaceDataRepository
        with tempfile.TemporaryDirectory() as d:
            db_path = str(Path(d) / "test.sqlite")
            db = RaceDB(db_path)
            db.create_tables()
            db.insert_race("2024-07-10", "KIRYU", 1, _minimal_race_data_with_result("KIRYU", 1))
            db.insert_odds("2024-07-10", "KIRYU", 1, {})
            db.insert_race("2024-07-10", "TODA", 1, _minimal_race_data_with_result("TODA", 1))
            db.insert_odds("2024-07-10", "TODA", 1, {})
            db.close()
            repo = DbRaceDataRepository(db_path)
            only_kiryu = repo.load_races_by_date("2024-07-10", venues=["KIRYU"])
            assert len(only_kiryu) == 1
            assert only_kiryu[0][1] == "KIRYU"
            repo.close()


class TestBaselineTrainDataSource:
    """baseline_train の data_source=json / db 切替"""

    def test_baseline_train_data_source_json(self, tmp_path):
        """data_source=json で従来と同じ動作（repository 経由）"""
        from kyotei_predictor.application.baseline_train_usecase import run_baseline_train
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        for i in range(3):
            (data_dir / f"race_data_2024-05-01_KIRYU_R{i+1}.json").write_text(
                json.dumps(_minimal_race_data_with_result("KIRYU", i + 1), ensure_ascii=False)
            )
        model_path = tmp_path / "model.joblib"
        summary = run_baseline_train(
            data_dir=data_dir,
            model_save_path=model_path,
            max_samples=10,
            n_estimators=3,
            max_depth=2,
            data_source="json",
        )
        assert summary["n_samples"] == 3
        assert model_path.exists()

    def test_baseline_train_data_source_db(self, tmp_path):
        """data_source=db で DB から学習できること"""
        from kyotei_predictor.data.race_db import RaceDB
        from kyotei_predictor.application.baseline_train_usecase import run_baseline_train
        db_path = str(tmp_path / "races.sqlite")
        db = RaceDB(db_path)
        db.create_tables()
        for i in range(1, 4):
            db.insert_race("2024-08-01", "EDOGAWA", i, _minimal_race_data_with_result("EDOGAWA", i))
            db.insert_odds("2024-08-01", "EDOGAWA", i, {})
        db.close()

        model_path = tmp_path / "model.joblib"
        summary = run_baseline_train(
            data_dir=tmp_path,
            model_save_path=model_path,
            max_samples=10,
            n_estimators=3,
            max_depth=2,
            data_source="db",
            db_path=db_path,
        )
        assert summary["n_samples"] == 3
        assert model_path.exists()

    def test_baseline_train_default_no_data_source(self, tmp_path):
        """data_source 未指定時は従来通り JSON 直読で動くこと"""
        from kyotei_predictor.application.baseline_train_usecase import run_baseline_train
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "race_data_2024-05-01_KIRYU_R1.json").write_text(
            json.dumps(_minimal_race_data_with_result(), ensure_ascii=False)
        )
        model_path = tmp_path / "model.joblib"
        summary = run_baseline_train(
            data_dir=data_dir,
            model_save_path=model_path,
            max_samples=10,
            n_estimators=2,
            max_depth=2,
        )
        assert summary["n_samples"] == 1


class TestRaceDataRepositoryFactory:
    """get_race_data_repository のテスト"""

    def test_factory_returns_json_repo(self, tmp_path):
        from kyotei_predictor.infrastructure.repositories.race_data_repository_factory import get_race_data_repository
        from kyotei_predictor.infrastructure.repositories.json_race_data_repository import JsonRaceDataRepository
        repo = get_race_data_repository("json", data_dir=tmp_path)
        assert isinstance(repo, JsonRaceDataRepository)

    def test_factory_returns_db_repo(self):
        import tempfile
        from kyotei_predictor.infrastructure.repositories.race_data_repository_factory import get_race_data_repository
        from kyotei_predictor.infrastructure.repositories.db_race_data_repository import DbRaceDataRepository
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            db_path = f.name
        try:
            repo = get_race_data_repository("db", db_path=db_path)
            assert isinstance(repo, DbRaceDataRepository)
        finally:
            Path(db_path).unlink(missing_ok=True)
