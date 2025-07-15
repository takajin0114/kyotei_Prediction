#!/usr/bin/env python3
"""
Web表示機能の自動テスト
HTML、CSS、JavaScriptの動作確認
"""

import unittest
import json
import tempfile
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
import threading
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

class TestWebDisplay(unittest.TestCase):
    """Web表示機能のテストクラス"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        cls.test_server_process = None
        cls.driver = None
        cls.test_data = cls.create_test_data()
        
    @classmethod
    def tearDownClass(cls):
        """テストクラスのクリーンアップ"""
        if cls.driver:
            cls.driver.quit()
        if cls.test_server_process:
            cls.test_server_process.terminate()
    
    @classmethod
    def create_test_data(cls):
        """テスト用の予測データを作成"""
        return {
            "prediction_date": "2024-07-15",
            "generated_at": "2025-07-15T10:00:00.000000",
            "model_info": {
                "model_path": "/test/model.zip",
                "model_name": "test_model",
                "version": "2025-07-15",
                "training_data_until": "2025-07-14"
            },
            "execution_summary": {
                "total_venues": 2,
                "total_races": 24,
                "successful_predictions": 24,
                "execution_time_minutes": 1.5,
                "data_fetched": True,
                "prediction_only": False
            },
            "predictions": [
                {
                    "venue": "TAMAGAWA",
                    "venue_code": "05",
                    "race_number": 1,
                    "race_time": "09:00",
                    "top_20_combinations": [
                        {
                            "combination": "1-2-3",
                            "probability": 0.85,
                            "expected_value": 2.5,
                            "rank": 1
                        },
                        {
                            "combination": "1-3-2",
                            "probability": 0.08,
                            "expected_value": -0.5,
                            "rank": 2
                        },
                        {
                            "combination": "2-1-3",
                            "probability": 0.05,
                            "expected_value": 1.2,
                            "rank": 3
                        }
                    ],
                    "total_probability": 0.98,
                    "purchase_suggestions": [
                        {
                            "type": "wheel",
                            "description": "1-流し",
                            "combinations": ["1-2-3", "1-3-2"],
                            "total_probability": 0.93,
                            "total_cost": 200,
                            "expected_return": 186.0
                        },
                        {
                            "type": "box",
                            "description": "1-2-3 ボックス",
                            "combinations": ["1-2-3", "1-3-2", "2-1-3"],
                            "total_probability": 0.98,
                            "total_cost": 600,
                            "expected_return": 588.0
                        }
                    ],
                    "risk_level": "LOW"
                },
                {
                    "venue": "KIRYU",
                    "venue_code": "01",
                    "race_number": 1,
                    "race_time": "09:00",
                    "top_20_combinations": [
                        {
                            "combination": "2-1-3",
                            "probability": 0.75,
                            "expected_value": 1.8,
                            "rank": 1
                        }
                    ],
                    "total_probability": 0.75,
                    "purchase_suggestions": [
                        {
                            "type": "nagashi",
                            "description": "2-1-流し",
                            "combinations": ["2-1-3"],
                            "total_probability": 0.75,
                            "total_cost": 100,
                            "expected_return": 75.0
                        }
                    ],
                    "risk_level": "MEDIUM"
                }
            ],
            "venue_summaries": [
                {
                    "venue": "TAMAGAWA",
                    "venue_code": "05",
                    "total_races": 12,
                    "average_probability": 0.85,
                    "max_expected_value": 15.2,
                    "risk_level": "LOW"
                },
                {
                    "venue": "KIRYU",
                    "venue_code": "01",
                    "total_races": 12,
                    "average_probability": 0.70,
                    "max_expected_value": 8.5,
                    "risk_level": "MEDIUM"
                }
            ]
        }
    
    def setUp(self):
        """各テストの初期化"""
        self.start_test_server()
        self.setup_webdriver()
    
    def tearDown(self):
        """各テストのクリーンアップ"""
        if self.driver:
            self.driver.quit()
    
    def start_test_server(self):
        """テストサーバーを起動"""
        # テスト用のJSONファイルを作成
        outputs_dir = PROJECT_ROOT / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        
        test_json_path = outputs_dir / "predictions_latest.json"
        with open(test_json_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f, ensure_ascii=False, indent=2)
        
        # テストサーバーを起動
        server_script = PROJECT_ROOT / "kyotei_predictor" / "static" / "test_server.py"
        self.test_server_process = subprocess.Popen(
            [sys.executable, str(server_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # サーバー起動を待機
        time.sleep(3)
    
    def setup_webdriver(self):
        """WebDriverの設定"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # ヘッドレスモード
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # ChromeDriverを自動ダウンロード
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
        except Exception as e:
            self.skipTest(f"WebDriverの初期化に失敗: {e}")
    
    def test_page_loads_successfully(self):
        """ページが正常に読み込まれることをテスト"""
        url = "http://localhost:8000/kyotei_predictor/templates/predictions.html"
        self.driver.get(url)
        
        # ページタイトルの確認
        self.assertIn("競艇予測結果表示", self.driver.title)
        
        # メインコンテンツの存在確認
        main_content = self.driver.find_element(By.ID, "main-content")
        self.assertTrue(main_content.is_displayed())
    
    def test_data_loading_and_display(self):
        """データの読み込みと表示をテスト"""
        url = "http://localhost:8000/kyotei_predictor/templates/predictions.html"
        self.driver.get(url)
        
        # ローディングが表示されることを確認
        loading = self.driver.find_element(By.ID, "loading")
        self.assertTrue(loading.is_displayed())
        
        # データ読み込み完了を待機
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "loading"))
        )
        
        # サマリー情報の確認
        summary_section = self.driver.find_element(By.ID, "summary-section")
        self.assertIn("TAMAGAWA", summary_section.text)
        self.assertIn("KIRYU", summary_section.text)
        self.assertIn("2", summary_section.text)  # 会場数
        self.assertIn("24", summary_section.text)  # レース数
    
    def test_venue_filter_functionality(self):
        """会場フィルター機能をテスト"""
        url = "http://localhost:8000/kyotei_predictor/templates/predictions.html"
        self.driver.get(url)
        
        # データ読み込み完了を待機
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "loading"))
        )
        
        # 会場フィルターの確認
        venue_filter = self.driver.find_element(By.ID, "venue-filter")
        options = venue_filter.find_elements(By.TAG_NAME, "option")
        
        # 全会場 + 2会場のオプションがあることを確認
        self.assertEqual(len(options), 3)  # 全会場 + TAMAGAWA + KIRYU
        
        # TAMAGAWAを選択
        venue_filter.send_keys("TAMAGAWA")
        
        # フィルター適用後の表示確認
        time.sleep(1)
        venues_section = self.driver.find_element(By.ID, "venues-section")
        self.assertIn("TAMAGAWA", venues_section.text)
        self.assertNotIn("KIRYU", venues_section.text)
    
    def test_risk_filter_functionality(self):
        """リスクフィルター機能をテスト"""
        url = "http://localhost:8000/kyotei_predictor/templates/predictions.html"
        self.driver.get(url)
        
        # データ読み込み完了を待機
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "loading"))
        )
        
        # リスクフィルターの確認
        risk_filter = self.driver.find_element(By.ID, "risk-filter")
        options = risk_filter.find_elements(By.TAG_NAME, "option")
        
        # 全て + 3リスクレベルのオプションがあることを確認
        self.assertEqual(len(options), 4)  # 全て + LOW + MEDIUM + HIGH
        
        # LOWリスクを選択
        risk_filter.send_keys("LOW")
        
        # フィルター適用後の表示確認
        time.sleep(1)
        venues_section = self.driver.find_element(By.ID, "venues-section")
        self.assertIn("TAMAGAWA", venues_section.text)  # LOWリスク
        self.assertNotIn("KIRYU", venues_section.text)  # MEDIUMリスク
    
    def test_race_details_expansion(self):
        """レース詳細の展開機能をテスト"""
        url = "http://localhost:8000/kyotei_predictor/templates/predictions.html"
        self.driver.get(url)
        
        # データ読み込み完了を待機
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "loading"))
        )
        
        # 最初のレースヘッダーをクリック
        race_headers = self.driver.find_elements(By.CLASS_NAME, "race-header")
        self.assertGreater(len(race_headers), 0)
        
        race_headers[0].click()
        time.sleep(1)
        
        # レース詳細が表示されることを確認
        race_details = self.driver.find_elements(By.CLASS_NAME, "race-details")
        self.assertGreater(len(race_details), 0)
        
        # 詳細が表示されていることを確認
        self.assertTrue(race_details[0].is_displayed())
    
    def test_combinations_table_display(self):
        """3連単組み合わせテーブルの表示をテスト"""
        url = "http://localhost:8000/kyotei_predictor/templates/predictions.html"
        self.driver.get(url)
        
        # データ読み込み完了を待機
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "loading"))
        )
        
        # 最初のレースを展開
        race_headers = self.driver.find_elements(By.CLASS_NAME, "race-header")
        race_headers[0].click()
        time.sleep(1)
        
        # テーブルの存在確認
        tables = self.driver.find_elements(By.TAG_NAME, "table")
        self.assertGreater(len(tables), 0)
        
        # 組み合わせデータの確認
        table = tables[0]
        rows = table.find_elements(By.TAG_NAME, "tr")
        self.assertGreater(len(rows), 1)  # ヘッダー + データ行
        
        # 1-2-3の組み合わせが表示されていることを確認
        table_text = table.text
        self.assertIn("1-2-3", table_text)
        self.assertIn("85.00%", table_text)  # 確率
        self.assertIn("2.5", table_text)     # 期待値
    
    def test_purchase_suggestions_display(self):
        """購入提案の表示をテスト"""
        url = "http://localhost:8000/kyotei_predictor/templates/predictions.html"
        self.driver.get(url)
        
        # データ読み込み完了を待機
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "loading"))
        )
        
        # 最初のレースを展開
        race_headers = self.driver.find_elements(By.CLASS_NAME, "race-header")
        race_headers[0].click()
        time.sleep(1)
        
        # 購入提案カードの存在確認
        suggestion_cards = self.driver.find_elements(By.CLASS_NAME, "suggestion-card")
        self.assertGreater(len(suggestion_cards), 0)
        
        # 提案内容の確認
        card_text = suggestion_cards[0].text
        self.assertIn("流し", card_text)
        self.assertIn("200", card_text)  # 購入金額
        self.assertIn("93.00%", card_text)  # 合計確率
    
    def test_responsive_design(self):
        """レスポンシブデザインをテスト"""
        url = "http://localhost:8000/kyotei_predictor/templates/predictions.html"
        self.driver.get(url)
        
        # データ読み込み完了を待機
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "loading"))
        )
        
        # デスクトップサイズでの表示確認
        self.driver.set_window_size(1920, 1080)
        time.sleep(1)
        
        # タブレットサイズでの表示確認
        self.driver.set_window_size(768, 1024)
        time.sleep(1)
        
        # モバイルサイズでの表示確認
        self.driver.set_window_size(375, 667)
        time.sleep(1)
        
        # ページが正常に表示されることを確認
        main_content = self.driver.find_element(By.ID, "main-content")
        self.assertTrue(main_content.is_displayed())
    
    def test_error_handling(self):
        """エラーハンドリングをテスト"""
        # 存在しないJSONファイルでテスト
        outputs_dir = PROJECT_ROOT / "outputs"
        backup_file = outputs_dir / "predictions_latest_backup.json"
        
        # 既存ファイルをバックアップ
        original_file = outputs_dir / "predictions_latest.json"
        if original_file.exists():
            original_file.rename(backup_file)
        
        try:
            url = "http://localhost:8000/kyotei_predictor/templates/predictions.html"
            self.driver.get(url)
            
            # エラーメッセージが表示されることを確認
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "error-message"))
            )
            
            error_message = self.driver.find_element(By.ID, "error-message")
            self.assertTrue(error_message.is_displayed())
            
        finally:
            # ファイルを復元
            if backup_file.exists():
                backup_file.rename(original_file)
    
    def test_css_styles_loaded(self):
        """CSSスタイルが正しく読み込まれていることをテスト"""
        url = "http://localhost:8000/kyotei_predictor/templates/predictions.html"
        self.driver.get(url)
        
        # Bootstrap CSSの読み込み確認
        bootstrap_link = self.driver.find_element(
            By.CSS_SELECTOR, 
            'link[href*="bootstrap"]'
        )
        self.assertIsNotNone(bootstrap_link)
        
        # Font Awesome CSSの読み込み確認
        fontawesome_link = self.driver.find_element(
            By.CSS_SELECTOR, 
            'link[href*="font-awesome"]'
        )
        self.assertIsNotNone(fontawesome_link)
        
        # カスタムCSSの読み込み確認
        custom_css_link = self.driver.find_element(
            By.CSS_SELECTOR, 
            'link[href*="predictions.css"]'
        )
        self.assertIsNotNone(custom_css_link)
    
    def test_javascript_functionality(self):
        """JavaScript機能をテスト"""
        url = "http://localhost:8000/kyotei_predictor/templates/predictions.html"
        self.driver.get(url)
        
        # データ読み込み完了を待機
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "loading"))
        )
        
        # JavaScriptが正常に動作していることを確認
        # 更新時刻が表示されていることを確認
        last_updated = self.driver.find_element(By.ID, "last-updated")
        self.assertIn("更新時刻:", last_updated.text)
        
        # 会場フィルターが動的に生成されていることを確認
        venue_filter = self.driver.find_element(By.ID, "venue-filter")
        options = venue_filter.find_elements(By.TAG_NAME, "option")
        self.assertGreater(len(options), 1)  # 全会場 + 会場オプション

class TestWebDisplayUnit(unittest.TestCase):
    """Web表示機能のユニットテスト"""
    
    def test_html_structure(self):
        """HTML構造のテスト"""
        html_file = PROJECT_ROOT / "kyotei_predictor" / "templates" / "predictions.html"
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 必要な要素の存在確認
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('<html lang="ja">', html_content)
        self.assertIn('<title>競艇予測結果表示</title>', html_content)
        self.assertIn('id="main-content"', html_content)
        self.assertIn('id="summary-section"', html_content)
        self.assertIn('id="venues-section"', html_content)
    
    def test_css_file_exists(self):
        """CSSファイルの存在確認"""
        css_file = PROJECT_ROOT / "kyotei_predictor" / "static" / "css" / "predictions.css"
        self.assertTrue(css_file.exists())
        
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # 必要なCSSクラスの存在確認
        self.assertIn('.venue-section', css_content)
        self.assertIn('.race-header', css_content)
        self.assertIn('.suggestion-card', css_content)
    
    def test_js_file_exists(self):
        """JavaScriptファイルの存在確認"""
        js_file = PROJECT_ROOT / "kyotei_predictor" / "static" / "js" / "predictions.js"
        self.assertTrue(js_file.exists())
        
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # 必要なJavaScriptクラスの存在確認
        self.assertIn('class PredictionsViewer', js_content)
        self.assertIn('loadPredictions', js_content)
        self.assertIn('renderPredictions', js_content)

if __name__ == '__main__':
    # テストの実行
    unittest.main(verbosity=2) 