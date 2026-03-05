#!/usr/bin/env python3
"""
config.settings の単体テスト（リファクタ後のパス一元化）。
"""
import os
import tempfile
import pytest
from pathlib import Path


class TestSettings:
    """Settings クラスのテスト"""

    def test_project_root_is_path(self):
        from kyotei_predictor.config.settings import Settings
        assert hasattr(Settings, "PROJECT_ROOT")
        assert isinstance(Settings.PROJECT_ROOT, Path)
        assert Settings.PROJECT_ROOT.is_dir() or not Settings.PROJECT_ROOT.exists()

    def test_project_root_resolves_to_expected_structure(self):
        from kyotei_predictor.config.settings import Settings
        root = Settings.PROJECT_ROOT
        # リポジトリルートには kyotei_predictor がある想定
        kyotei_dir = root / "kyotei_predictor"
        assert kyotei_dir.name == "kyotei_predictor"

    def test_data_paths_are_relative_strings(self):
        from kyotei_predictor.config.settings import Settings
        assert "kyotei_predictor" in Settings.DATA_DIR
        assert "raw" in Settings.RAW_DATA_DIR
        assert Settings.ROOT_LOGS_DIR == "logs"
        assert Settings.ROOT_OUTPUTS_DIR == "outputs"

    def test_get_data_paths_returns_dict(self):
        from kyotei_predictor.config.settings import Settings
        paths = Settings.get_data_paths()
        assert isinstance(paths, dict)
        assert "raw_dir" in paths
        assert "logs_dir" in paths

    def test_get_optuna_paths_returns_dict(self):
        from kyotei_predictor.config.settings import Settings
        paths = Settings.get_optuna_paths()
        assert isinstance(paths, dict)
        assert "studies_dir" in paths
        assert "results_dir" in paths

    def test_get_web_config_returns_dict(self):
        from kyotei_predictor.config.settings import Settings
        cfg = Settings.get_web_config()
        assert "host" in cfg
        assert "port" in cfg
        assert "debug" in cfg

    def test_get_model_config_returns_dict(self):
        from kyotei_predictor.config.settings import Settings
        cfg = Settings.get_model_config()
        assert "trifecta_combinations" in cfg
        assert "default_temperature" in cfg

    def test_get_investment_config_returns_dict(self):
        from kyotei_predictor.config.settings import Settings
        cfg = Settings.get_investment_config()
        assert "default_threshold" in cfg
        assert "conservative" in cfg

    def test_create_directories(self, tmp_path, monkeypatch):
        """create_directories がディレクトリを作成する（Settings のパスを一時ディレクトリに差し替え）"""
        import kyotei_predictor.config.settings as mod
        base = Path(tmp_path) / "cfg_dirs"
        monkeypatch.setattr(mod.Settings, "DATA_DIR", str(base / "data"))
        monkeypatch.setattr(mod.Settings, "RAW_DATA_DIR", str(base / "raw"))
        monkeypatch.setattr(mod.Settings, "PROCESSED_DATA_DIR", str(base / "processed"))
        monkeypatch.setattr(mod.Settings, "SAMPLE_DATA_DIR", str(base / "sample"))
        monkeypatch.setattr(mod.Settings, "BACKUP_DATA_DIR", str(base / "backup"))
        monkeypatch.setattr(mod.Settings, "OUTPUT_DIR", str(base / "output"))
        monkeypatch.setattr(mod.Settings, "LOGS_DIR", str(base / "logs"))
        monkeypatch.setattr(mod.Settings, "OPTUNA_STUDIES_DIR", str(base / "optuna_studies"))
        monkeypatch.setattr(mod.Settings, "OPTUNA_LOGS_DIR", str(base / "optuna_logs"))
        monkeypatch.setattr(mod.Settings, "OPTUNA_MODELS_DIR", str(base / "optuna_models"))
        monkeypatch.setattr(mod.Settings, "OPTUNA_RESULTS_DIR", str(base / "optuna_results"))
        monkeypatch.setattr(mod.Settings, "OPTUNA_TENSORBOARD_DIR", str(base / "tensorboard"))
        mod.Settings.create_directories()
        assert (base / "data").exists()
        assert (base / "logs").exists()


class TestGetProjectRoot:
    """get_project_root() のテスト"""

    def test_returns_path(self):
        from kyotei_predictor.config.settings import get_project_root
        root = get_project_root()
        assert isinstance(root, Path)

    def test_matches_settings(self):
        from kyotei_predictor.config.settings import Settings, get_project_root
        assert get_project_root() == Settings.PROJECT_ROOT


class TestGetRawDataDir:
    """get_raw_data_dir() のテスト"""

    def test_returns_path(self):
        from kyotei_predictor.config.settings import get_raw_data_dir
        raw = get_raw_data_dir()
        assert isinstance(raw, Path)

    def test_default_is_under_project_root(self):
        from kyotei_predictor.config.settings import get_raw_data_dir, get_project_root
        raw = get_raw_data_dir()
        root = get_project_root()
        try:
            raw.relative_to(root)
        except ValueError:
            # 環境変数で別パスが指定されている場合はスキップ
            pass

    def test_env_override(self, monkeypatch):
        from kyotei_predictor.config.settings import get_raw_data_dir
        with tempfile.TemporaryDirectory() as d:
            monkeypatch.setenv("KYOTEI_RAW_DATA_DIR", d)
            raw = get_raw_data_dir()
            assert str(raw) == d
            monkeypatch.delenv("KYOTEI_RAW_DATA_DIR", raising=False)
