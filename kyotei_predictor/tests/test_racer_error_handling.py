#!/usr/bin/env python3
"""
選手名取得エラーハンドリングのテスト
改善されたエラーハンドリング機能をテストする
"""

import unittest
from unittest.mock import Mock, patch
from io import StringIO
import json
import tempfile
import os
from datetime import date
from metaboatrace.models.stadium import StadiumTelCode

from kyotei_predictor.tools.fetch.race_data_fetcher import (
    safe_extract_racers,
    safe_extract_race_entries,
    safe_extract_racer_performances,
    safe_extract_boat_performances,
    safe_extract_motor_performances
)

class TestRacerErrorHandling(unittest.TestCase):
    """選手名取得エラーハンドリングのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.test_html = StringIO("<html><body>テストHTML</body></html>")
    
    def test_safe_extract_racers_success(self):
        """選手データ取得成功のテスト"""
        with patch('kyotei_predictor.tools.fetch.race_data_fetcher.entry_scraping.extract_racers') as mock_extract:
            mock_racer = Mock()
            mock_racer.last_name = "田中"
            mock_racer.first_name = "太郎"
            mock_extract.return_value = [mock_racer]
            
            result = safe_extract_racers(self.test_html)
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].last_name, "田中")
            self.assertEqual(result[0].first_name, "太郎")
    
    def test_safe_extract_racers_value_error_retry(self):
        """選手名解析エラー時のリトライテスト"""
        with patch('kyotei_predictor.tools.fetch.race_data_fetcher.entry_scraping.extract_racers') as mock_extract:
            # 1回目はエラー、2回目は成功
            mock_extract.side_effect = [
                ValueError("not enough values to unpack (expected 2, got 1)"),
                [Mock(last_name="田中", first_name="太郎")]
            ]
            
            result = safe_extract_racers(self.test_html, max_retries=2)
            
            self.assertEqual(len(result), 1)
            self.assertEqual(mock_extract.call_count, 2)
    
    def test_safe_extract_racers_max_retries_exceeded(self):
        """最大リトライ回数超過のテスト"""
        with patch('kyotei_predictor.tools.fetch.race_data_fetcher.entry_scraping.extract_racers') as mock_extract:
            mock_extract.side_effect = ValueError("not enough values to unpack (expected 2, got 1)")
            
            result = safe_extract_racers(self.test_html, max_retries=2)
            
            self.assertEqual(result, [])
            self.assertEqual(mock_extract.call_count, 2)
    
    def test_safe_extract_racers_empty_result(self):
        """空の結果に対するテスト"""
        with patch('kyotei_predictor.tools.fetch.race_data_fetcher.entry_scraping.extract_racers') as mock_extract:
            mock_extract.return_value = []
            
            result = safe_extract_racers(self.test_html, max_retries=2)
            
            self.assertEqual(result, [])
    
    def test_safe_extract_race_entries_success(self):
        """レース出走データ取得成功のテスト"""
        with patch('kyotei_predictor.tools.fetch.race_data_fetcher.entry_scraping.extract_race_entries') as mock_extract:
            mock_entry = Mock()
            mock_entry.pit_number = 1
            mock_extract.return_value = [mock_entry]
            
            result = safe_extract_race_entries(self.test_html)
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].pit_number, 1)
    
    def test_safe_extract_race_entries_error_retry(self):
        """レース出走データ取得エラー時のリトライテスト"""
        with patch('kyotei_predictor.tools.fetch.race_data_fetcher.entry_scraping.extract_race_entries') as mock_extract:
            mock_extract.side_effect = [
                Exception("Network error"),
                [Mock(pit_number=1)]
            ]
            
            result = safe_extract_race_entries(self.test_html, max_retries=2)
            
            self.assertEqual(len(result), 1)
            self.assertEqual(mock_extract.call_count, 2)
    
    def test_safe_extract_racer_performances_success(self):
        """選手成績データ取得成功のテスト"""
        with patch('kyotei_predictor.tools.fetch.race_data_fetcher.entry_scraping.extract_racer_performances') as mock_extract:
            mock_perf = Mock()
            mock_perf.rate_in_all_stadium = 0.75
            mock_extract.return_value = [mock_perf]
            
            result = safe_extract_racer_performances(self.test_html)
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].rate_in_all_stadium, 0.75)
    
    def test_safe_extract_boat_performances_success(self):
        """ボート成績データ取得成功のテスト"""
        with patch('kyotei_predictor.tools.fetch.race_data_fetcher.entry_scraping.extract_boat_performances') as mock_extract:
            mock_perf = Mock()
            mock_perf.number = "1234"
            mock_extract.return_value = [mock_perf]
            
            result = safe_extract_boat_performances(self.test_html)
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].number, "1234")
    
    def test_safe_extract_motor_performances_success(self):
        """モーター成績データ取得成功のテスト"""
        with patch('kyotei_predictor.tools.fetch.race_data_fetcher.entry_scraping.extract_motor_performances') as mock_extract:
            mock_perf = Mock()
            mock_perf.number = "5678"
            mock_extract.return_value = [mock_perf]
            
            result = safe_extract_motor_performances(self.test_html)
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].number, "5678")
    
    def test_html_file_seek_reset(self):
        """HTMLファイルのポインタリセットテスト"""
        with patch('kyotei_predictor.tools.fetch.race_data_fetcher.entry_scraping.extract_racers') as mock_extract:
            mock_extract.side_effect = [
                ValueError("not enough values to unpack"),
                [Mock(last_name="田中", first_name="太郎")]
            ]
            
            safe_extract_racers(self.test_html, max_retries=2)
            
            # HTMLファイルのseekが呼ばれていることを確認
            self.assertGreater(self.test_html.seek.call_count, 0)

class TestRacerErrorLogging(unittest.TestCase):
    """選手名取得エラーログ機能のテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_error_log_creation(self):
        """エラーログファイル作成のテスト"""
        from kyotei_predictor.tools.batch.batch_fetch_all_venues import log_racer_error
        
        error_info = {
            "timestamp": "2024-01-01T00:00:00",
            "stadium": "TEST",
            "date": "2024-01-01",
            "race_no": 1,
            "error_type": "racer_name_parse_error",
            "error_message": "test error"
        }
        
        # ログディレクトリを一時ディレクトリに変更
        with patch('kyotei_predictor.tools.batch.batch_fetch_all_venues.os.path.join') as mock_join:
            mock_join.return_value = self.temp_dir
            
            log_racer_error(error_info)
            
            # ログファイルが作成されていることを確認
            log_files = [f for f in os.listdir(self.temp_dir) if f.startswith('racer_errors_')]
            self.assertGreater(len(log_files), 0)

if __name__ == '__main__':
    unittest.main() 