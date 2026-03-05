#!/usr/bin/env python3
"""
verify_race_data_simple のリファクタ後テスト（_get_data_dir / rglob）。
"""
from pathlib import Path
import pytest


class TestVerifyRaceDataSimpleRefactor:
    """リファクタ後の verify_race_data_simple の単体テスト"""

    def test_get_data_dir_returns_path(self):
        """_get_data_dir は Path を返す"""
        from kyotei_predictor.tools.analysis.verify_race_data_simple import _get_data_dir
        p = _get_data_dir()
        assert isinstance(p, Path)

    def test_module_imports_successfully(self):
        """モジュールがインポートできる（Settings 依存が解決する）"""
        from kyotei_predictor.tools.analysis import verify_race_data_simple
        assert hasattr(verify_race_data_simple, "verify_race_data_integrity")
        assert hasattr(verify_race_data_simple, "_get_data_dir")
