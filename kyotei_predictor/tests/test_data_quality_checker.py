#!/usr/bin/env python3
"""tools.data_quality_checker の単体テスト"""
from pathlib import Path
from unittest.mock import patch

import pytest


class TestDataQualityChecker:
    def test_import_and_class_exists(self):
        from kyotei_predictor.tools.data_quality_checker import DataQualityChecker
        assert DataQualityChecker is not None

    def test_check_data_availability_no_data(self, tmp_path):
        from kyotei_predictor.tools.data_quality_checker import DataQualityChecker
        with patch("kyotei_predictor.tools.data_quality_checker.DATA_DIR", tmp_path):
            checker = DataQualityChecker()
            result = checker.check_data_availability("2024-99-99")
        assert result["status"] == "no_data"
        assert "データディレクトリが存在しません" in result["message"]
