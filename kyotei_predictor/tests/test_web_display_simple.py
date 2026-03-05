#!/usr/bin/env python3
"""
Web表示機能の軽量自動テスト
HTML、CSS、JavaScriptの基本動作確認（Selenium不使用）
"""

import unittest
import json
import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

class TestWebDisplaySimple(unittest.TestCase):
    """Web表示機能の軽量テストクラス"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        cls.test_server_process = None
        cls.test_data = cls.create_test_data()
        
    @classmethod
    def tearDownClass(cls):
        """テストクラスのクリーンアップ"""
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
                    "all_combinations": [
                        {
                            "combination": "1-2-3",
                            "probability": 0.85,
                            "expected_value": 2.5,
                            "rank": 1
                        }
                    ]
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
                }
            ]
        }
    
    def setUp(self):
        """各テストの初期化"""
        self.start_test_server()
    
    def tearDown(self):
        """各テストのクリーンアップ"""
        pass
    
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
    
    def test_server_running(self):
        """テストサーバーが正常に起動していることをテスト"""
        try:
            response = requests.get("http://localhost:8000", timeout=5)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException as e:
            self.fail(f"テストサーバーに接続できません: {e}")
    
    def test_html_file_accessible(self):
        """HTMLファイルがアクセス可能であることをテスト"""
        try:
            response = requests.get(
                "http://localhost:8000/kyotei_predictor/templates/predictions.html",
                timeout=5
            )
            self.assertEqual(response.status_code, 200)
            # 明示的にUTF-8でデコード
            content = response.content.decode('utf-8')
            self.assertIn("競艇予測結果表示", content)
        except requests.exceptions.RequestException as e:
            self.fail(f"HTMLファイルにアクセスできません: {e}")
        except UnicodeDecodeError as e:
            self.fail(f"HTMLファイルのデコードに失敗: {e}")
    
    def test_json_data_accessible(self):
        """JSONデータがアクセス可能であることをテスト"""
        try:
            response = requests.get(
                "http://localhost:8000/outputs/predictions_latest.json",
                timeout=5
            )
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertEqual(data["prediction_date"], "2024-07-15")
            self.assertEqual(data["execution_summary"]["total_venues"], 2)
            self.assertEqual(len(data["predictions"]), 1)
            
        except requests.exceptions.RequestException as e:
            self.fail(f"JSONデータにアクセスできません: {e}")
        except json.JSONDecodeError as e:
            self.fail(f"JSONデータの解析に失敗: {e}")
    
    def test_css_file_accessible(self):
        """CSSファイルがアクセス可能であることをテスト"""
        try:
            response = requests.get(
                "http://localhost:8000/kyotei_predictor/static/css/predictions.css",
                timeout=5
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(".venue-section", response.text)
            self.assertIn(".race-header", response.text)
            
        except requests.exceptions.RequestException as e:
            self.fail(f"CSSファイルにアクセスできません: {e}")
    
    def test_js_file_accessible(self):
        """JavaScriptファイルがアクセス可能であることをテスト"""
        try:
            response = requests.get(
                "http://localhost:8000/kyotei_predictor/static/js/predictions.js",
                timeout=5
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("class PredictionsViewer", response.text)
            self.assertIn("loadPredictions", response.text)
            
        except requests.exceptions.RequestException as e:
            self.fail(f"JavaScriptファイルにアクセスできません: {e}")
    
    def test_external_resources_accessible(self):
        """外部リソース（Bootstrap、Font Awesome）がアクセス可能であることをテスト"""
        try:
            # Bootstrap CSS
            response = requests.get(
                "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
                timeout=10
            )
            self.assertEqual(response.status_code, 200)
            
            # Font Awesome CSS
            response = requests.get(
                "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
                timeout=10
            )
            self.assertEqual(response.status_code, 200)
            
        except requests.exceptions.RequestException as e:
            self.fail(f"外部リソースにアクセスできません: {e}")

class TestWebDisplayFiles(unittest.TestCase):
    """Web表示機能のファイル構造テスト"""
    
    def test_html_file_exists(self):
        """HTMLファイルが存在することをテスト"""
        html_file = PROJECT_ROOT / "kyotei_predictor" / "templates" / "predictions.html"
        self.assertTrue(html_file.exists(), f"HTMLファイルが存在しません: {html_file}")
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 必要な要素の存在確認
        self.assertIn('<!DOCTYPE html>', content)
        self.assertIn('<html lang="ja">', content)
        self.assertIn('<title>競艇予測結果表示</title>', content)
        self.assertIn('id="main-content"', content)
        self.assertIn('id="summary-section"', content)
        self.assertIn('id="venues-section"', content)
        self.assertIn('id="venue-filter"', content)
        self.assertIn('id="risk-filter"', content)
    
    def test_css_file_exists(self):
        """CSSファイルが存在することをテスト"""
        css_file = PROJECT_ROOT / "kyotei_predictor" / "static" / "css" / "predictions.css"
        self.assertTrue(css_file.exists(), f"CSSファイルが存在しません: {css_file}")
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 必要なCSSクラスの存在確認
        self.assertIn('.venue-section', content)
        self.assertIn('.race-header', content)
        self.assertIn('.suggestion-card', content)
        self.assertIn('.probability-bar', content)
        self.assertIn('.expected-value', content)
        self.assertIn('@media', content)  # レスポンシブ対応
    
    def test_js_file_exists(self):
        """JavaScriptファイルが存在することをテスト"""
        js_file = PROJECT_ROOT / "kyotei_predictor" / "static" / "js" / "predictions.js"
        self.assertTrue(js_file.exists(), f"JavaScriptファイルが存在しません: {js_file}")
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 必要なJavaScriptクラスとメソッドの存在確認
        self.assertIn('class PredictionsViewer', content)
        self.assertIn('loadPredictions', content)
        self.assertIn('renderPredictions', content)
        self.assertIn('filterData', content)
        self.assertIn('renderVenues', content)
        self.assertIn('renderSummary', content)
    
    def test_test_server_exists(self):
        """テストサーバーファイルが存在することをテスト"""
        server_file = PROJECT_ROOT / "kyotei_predictor" / "static" / "test_server.py"
        self.assertTrue(server_file.exists(), f"テストサーバーファイルが存在しません: {server_file}")
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 必要な機能の存在確認
        self.assertIn('class CustomHTTPRequestHandler', content)
        self.assertIn('CORS', content)
        self.assertIn('8000', content)

class TestWebDisplayContent(unittest.TestCase):
    """Web表示機能のコンテンツテスト"""
    
    def test_html_structure_validity(self):
        """HTML構造の妥当性をテスト"""
        html_file = PROJECT_ROOT / "kyotei_predictor" / "templates" / "predictions.html"
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本的なHTML構造の確認
        self.assertIn('<head>', content)
        self.assertIn('</head>', content)
        self.assertIn('<body>', content)
        self.assertIn('</body>', content)
        self.assertIn('</html>', content)
        
        # メタタグの確認
        self.assertIn('<meta charset="UTF-8">', content)
        self.assertIn('<meta name="viewport"', content)
        
        # 外部リソースの読み込み確認
        self.assertIn('bootstrap', content)
        self.assertIn('font-awesome', content)
        self.assertIn('predictions.css', content)
        self.assertIn('predictions.js', content)
    
    def test_css_structure_validity(self):
        """CSS構造の妥当性をテスト"""
        css_file = PROJECT_ROOT / "kyotei_predictor" / "static" / "css" / "predictions.css"
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # CSS変数の確認
        self.assertIn(':root', content)
        self.assertIn('--primary-blue', content)
        self.assertIn('--success-green', content)
        
        # レスポンシブ対応の確認
        self.assertIn('@media (max-width:', content)
        
        # アニメーションの確認
        self.assertIn('@keyframes', content)
        self.assertIn('animation:', content)
    
    def test_js_structure_validity(self):
        """JavaScript構造の妥当性をテスト"""
        js_file = PROJECT_ROOT / "kyotei_predictor" / "static" / "js" / "predictions.js"
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # ES6+ クラス構文の確認
        self.assertIn('class PredictionsViewer', content)
        self.assertIn('constructor', content)
        
        # 非同期処理の確認
        self.assertIn('async', content)
        self.assertIn('await', content)
        
        # イベントリスナーの確認
        self.assertIn('addEventListener', content)
        
        # DOM操作の確認
        self.assertIn('getElementById', content)
        self.assertIn('innerHTML', content)

if __name__ == '__main__':
    # テストの実行
    unittest.main(verbosity=2) 