#!/usr/bin/env python3
"""
統合ユーティリティのテスト
"""
import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

from kyotei_predictor.utils import (
    KyoteiUtils, Config, setup_logger, VenueMapper,
    KyoteiError, DataError, APIError
)
from kyotei_predictor.utils.logger import get_logger
from metaboatrace.models.stadium import StadiumTelCode

class TestKyoteiUtils:
    """KyoteiUtilsクラスのテスト"""
    
    def test_load_json_file_success(self):
        """JSONファイル読み込み成功テスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {"test": "data", "number": 123}
            json.dump(test_data, f)
            f.flush()
            
            result = KyoteiUtils.load_json_file(f.name)
            assert result == test_data
            
        os.unlink(f.name)
    
    def test_load_json_file_error(self):
        """JSONファイル読み込みエラーテスト"""
        result = KyoteiUtils.load_json_file("nonexistent_file.json")
        assert result == {}
    
    def test_save_json_file_success(self):
        """JSONファイル保存成功テスト"""
        test_data = {"test": "data", "number": 123}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.json")
            result = KyoteiUtils.save_json_file(test_data, file_path)
            
            assert result is True
            assert os.path.exists(file_path)
            
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)
                assert loaded_data == test_data
    
    def test_extract_race_result(self):
        """レース結果抽出テスト"""
        race_data = {
            "boats": [
                {"boat_number": 1, "arrival": 1},
                {"boat_number": 2, "arrival": 2},
                {"boat_number": 3, "arrival": 3},
                {"boat_number": 4, "arrival": 4},
                {"boat_number": 5, "arrival": 5},
                {"boat_number": 6, "arrival": 6}
            ]
        }
        
        result = KyoteiUtils.extract_race_result(race_data)
        assert result == (1, 2, 3)
    
    def test_calculate_expected_value(self):
        """期待値計算テスト"""
        result = KyoteiUtils.calculate_expected_value(0.5, 2.0)
        assert result == 1.0
    
    def test_is_profitable(self):
        """投資価値判定テスト"""
        assert KyoteiUtils.is_profitable(1.2) is True
        assert KyoteiUtils.is_profitable(0.8) is False
    
    def test_normalize_probabilities(self):
        """確率正規化テスト"""
        probs = [0.2, 0.3, 0.5]
        normalized = KyoteiUtils.normalize_probabilities(probs)
        assert sum(normalized) == pytest.approx(1.0)
        assert len(normalized) == 3

class TestConfig:
    """Configクラスのテスト"""
    
    def test_default_config(self):
        """デフォルト設定テスト"""
        config = Config()
        assert config.get_data_dir() == "data/raw"
        assert config.get_api_timeout() == 30
        assert config.get_retry_count() == 3
    
    def test_config_with_file(self):
        """設定ファイル読み込みテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "data": {"raw_dir": "custom/data"},
                "api": {"timeout": 60}
            }
            json.dump(test_config, f)
            f.flush()
            
            config = Config(f.name)
            assert config.get_data_dir() == "custom/data"
            assert config.get_api_timeout() == 60
            
        os.unlink(f.name)
    
    def test_env_overrides(self):
        """環境変数オーバーライドテスト"""
        with patch.dict(os.environ, {'KYOTEI_DATA_RAW_DIR': 'env/data'}):
            config = Config()
            assert config.get_data_dir() == "env/data"

class TestVenueMapper:
    """VenueMapperクラスのテスト"""
    
    def test_get_venue_name(self):
        """会場名取得テスト"""
        name = VenueMapper.get_venue_name(StadiumTelCode.KIRYU)
        assert name == "桐生"
    
    def test_get_venue_code(self):
        """会場コード取得テスト"""
        code = VenueMapper.get_venue_code(StadiumTelCode.KIRYU)
        assert code == "01"
    
    def test_get_venue_region(self):
        """会場地域取得テスト"""
        region = VenueMapper.get_venue_region(StadiumTelCode.KIRYU)
        assert region == "関東"
    
    def test_get_all_stadiums(self):
        """全競艇場取得テスト"""
        stadiums = VenueMapper.get_all_stadiums()
        assert len(stadiums) == 24
        assert StadiumTelCode.KIRYU in stadiums
    
    def test_get_stadium_by_code(self):
        """コードから会場取得テスト"""
        stadium = VenueMapper.get_stadium_by_code("01")
        assert stadium == StadiumTelCode.KIRYU
    
    def test_get_stadiums_by_region(self):
        """地域別会場取得テスト"""
        kanto_stadiums = VenueMapper.get_stadiums_by_region("関東")
        assert len(kanto_stadiums) > 0
        for stadium in kanto_stadiums:
            assert VenueMapper.get_venue_region(stadium) == "関東"

class TestExceptions:
    """例外クラスのテスト"""
    
    def test_kyotei_error(self):
        """KyoteiErrorテスト"""
        error = KyoteiError("テストエラー", "TEST_001", {"detail": "test"})
        assert error.message == "テストエラー"
        assert error.error_code == "TEST_001"
        assert error.details == {"detail": "test"}
    
    def test_data_error(self):
        """DataErrorテスト"""
        error = DataError("データエラー")
        assert isinstance(error, KyoteiError)
        assert error.message == "データエラー"
    
    def test_api_error(self):
        """APIErrorテスト"""
        error = APIError("APIエラー")
        assert isinstance(error, KyoteiError)
        assert error.message == "APIエラー"

class TestLogger:
    """ログ機能のテスト"""
    
    def test_setup_logger(self):
        """ログ設定テスト"""
        logger = setup_logger("test_logger", "INFO")
        assert logger.name == "test_logger"
        assert logger.level == 20  # INFO level
    
    def test_get_logger(self):
        """ロガー取得テスト"""
        logger = get_logger("test_get_logger")
        assert logger.name == "test_get_logger"

if __name__ == "__main__":
    pytest.main([__file__]) 