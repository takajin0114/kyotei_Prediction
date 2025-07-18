"""
システムステータスページのテスト
HTML/CSS/JSファイルの存在確認、HTTPサーバーでの表示確認、JavaScript機能のテスト
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestSystemStatusPage:
    """システムステータスページのテストクラス"""
    
    def setup_method(self):
        """テスト前のセットアップ"""
        self.base_dir = project_root / "kyotei_predictor"
        self.templates_dir = self.base_dir / "templates"
        self.static_dir = self.base_dir / "static"
        self.css_dir = self.static_dir / "css"
        self.js_dir = self.static_dir / "js"
        
        # テスト用HTTPサーバーのポート
        self.test_port = 8001
        self.base_url = f"http://localhost:{self.test_port}"
        
        # テストサーバープロセス
        self.server_process = None

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if self.server_process:
            self.stop_test_server()

    def test_required_files_exist(self):
        """必要なファイルが存在することを確認"""
        required_files = [
            self.templates_dir / "system_status.html",
            self.css_dir / "system_status.css",
            self.js_dir / "system_status.js"
        ]
        
        for file_path in required_files:
            assert file_path.exists(), f"ファイルが存在しません: {file_path}"
            assert file_path.stat().st_size > 0, f"ファイルが空です: {file_path}"

    def test_html_structure(self):
        """HTMLファイルの構造を確認"""
        html_file = self.templates_dir / "system_status.html"
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本的なHTML要素の確認
        assert '<!DOCTYPE html>' in content
        assert '<html lang="ja">' in content
        assert '<title>システムステータス - 競艇予測システム</title>' in content
        
        # Bootstrap 5の読み込み確認
        assert 'bootstrap@5.3.0' in content
        assert 'font-awesome' in content
        
        # 必要なCSS/JSファイルの読み込み確認
        assert 'system_status.css' in content
        assert 'system_status.js' in content
        
        # 主要なHTML要素の確認
        assert 'navbar' in content
        assert 'container-fluid' in content
        assert 'card' in content
        assert 'progress' in content
        
        # 必要なID要素の確認
        required_ids = [
            'refreshBtn', 'lastUpdate', 'systemStatus', 'systemStatusIcon',
            'batchProgress', 'batchProgressDetail', 'errorCount', 'lastExecution',
            'progressChart', 'venueProgress', 'dateProgress', 'modelInfo',
            'errorLogs', 'batchHistory', 'dataQuality', 'loadingOverlay'
        ]
        
        for element_id in required_ids:
            assert f'id="{element_id}"' in content, f"ID要素が見つかりません: {element_id}"

    def test_css_structure(self):
        """CSSファイルの構造を確認"""
        css_file = self.css_dir / "system_status.css"
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # CSS変数の確認
        assert ':root {' in content
        assert '--primary-color:' in content
        assert '--success-color:' in content
        assert '--danger-color:' in content
        
        # 主要なスタイルクラスの確認
        required_classes = [
            '.navbar', '.card', '.progress', '.btn', '.error-log-item',
            '.batch-history-item', '.model-info-item', '.data-quality-item'
        ]
        
        for class_name in required_classes:
            assert class_name in content, f"CSSクラスが見つかりません: {class_name}"
        
        # レスポンシブ対応の確認
        assert '@media (max-width:' in content
        assert 'backdrop-filter' in content

    def test_javascript_structure(self):
        """JavaScriptファイルの構造を確認"""
        js_file = self.js_dir / "system_status.js"
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # クラス定義の確認
        assert 'class SystemStatusManager' in content
        
        # 主要なメソッドの確認
        required_methods = [
            'init()', 'refreshData()', 'fetchSystemStatus()', 'fetchBatchProgress()',
            'updateSystemStatus()', 'updateBatchProgress()', 'updateErrorLogs()',
            'updateBatchHistory()', 'updateModelInfo()', 'updateDataQuality()'
        ]
        
        for method in required_methods:
            assert method in content, f"メソッドが見つかりません: {method}"
        
        # イベントリスナーの確認
        assert 'addEventListener' in content
        assert 'DOMContentLoaded' in content

    def start_test_server(self):
        """テスト用HTTPサーバーを開始"""
        try:
            # 既存のプロセスを停止
            self.stop_test_server()
            
            # 新しいサーバーを開始
            cmd = [
                sys.executable, "-m", "http.server", str(self.test_port),
                "--directory", str(project_root)
            ]
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # サーバー起動を待機
            time.sleep(2)
            
            # サーバーが起動しているか確認
            try:
                response = requests.get(f"{self.base_url}/", timeout=5)
                assert response.status_code == 200
            except requests.RequestException:
                raise Exception("テストサーバーの起動に失敗しました")
                
        except Exception as e:
            self.stop_test_server()
            raise e

    def stop_test_server(self):
        """テスト用HTTPサーバーを停止"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            finally:
                self.server_process = None

    def test_http_server_accessibility(self):
        """HTTPサーバーでのアクセス確認"""
        self.start_test_server()
        
        try:
            # システムステータスページへのアクセス
            url = f"{self.base_url}/kyotei_predictor/templates/system_status.html"
            response = requests.get(url, timeout=10)
            
            assert response.status_code == 200, f"HTTPステータスエラー: {response.status_code}"
            assert 'システムステータス' in response.text
            assert '競艇予測システム' in response.text
            
            # CSSファイルへのアクセス
            css_url = f"{self.base_url}/kyotei_predictor/static/css/system_status.css"
            css_response = requests.get(css_url, timeout=10)
            assert css_response.status_code == 200
            
            # JSファイルへのアクセス
            js_url = f"{self.base_url}/kyotei_predictor/static/js/system_status.js"
            js_response = requests.get(js_url, timeout=10)
            assert js_response.status_code == 200
            
        finally:
            self.stop_test_server()

    def test_javascript_functionality(self):
        """JavaScript機能のテスト（モック使用）"""
        js_file = self.js_dir / "system_status.js"
        
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # 基本的なJavaScript構文チェック
        # 実際のブラウザ環境でのテストはSeleniumを使用
        
        # モックデータの構造確認
        mock_data_patterns = [
            'status: \'online\'',
            'completed: 804',
            'total: 4152',
            'percentage: 19.4'
        ]
        
        for pattern in mock_data_patterns:
            assert pattern in js_content, f"モックデータパターンが見つかりません: {pattern}"

    def test_responsive_design(self):
        """レスポンシブデザインの確認"""
        css_file = self.css_dir / "system_status.css"
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # レスポンシブブレークポイントの確認
        responsive_queries = [
            '@media (max-width: 768px)',
            '@media (max-width: 576px)'
        ]
        
        for query in responsive_queries:
            assert query in content, f"レスポンシブクエリが見つかりません: {query}"

    def test_error_handling(self):
        """エラーハンドリングの確認"""
        js_file = self.js_dir / "system_status.js"
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # エラーハンドリング機能の確認
        error_handling_patterns = [
            'try {',
            'catch (error)',
            'console.error',
            'showError('
        ]
        
        for pattern in error_handling_patterns:
            assert pattern in content, f"エラーハンドリングパターンが見つかりません: {pattern}"

    def test_auto_refresh_functionality(self):
        """自動更新機能の確認"""
        js_file = self.js_dir / "system_status.js"
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 自動更新機能の確認
        auto_refresh_patterns = [
            'setInterval',
            'clearInterval',
            'refreshInterval',
            'autoRefreshEnabled'
        ]
        
        for pattern in auto_refresh_patterns:
            assert pattern in content, f"自動更新パターンが見つかりません: {pattern}"

    def test_accessibility_features(self):
        """アクセシビリティ機能の確認"""
        html_file = self.templates_dir / "system_status.html"
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # アクセシビリティ要素の確認
        accessibility_patterns = [
            'aria-valuenow',
            'aria-valuemin',
            'aria-valuemax',
            'role="progressbar"',
            'visually-hidden'
        ]
        
        for pattern in accessibility_patterns:
            assert pattern in content, f"アクセシビリティ要素が見つかりません: {pattern}"

def run_system_status_tests():
    """システムステータスページのテストを実行"""
    import pytest
    
    test_file = Path(__file__)
    print(f"システムステータスページのテストを実行中: {test_file}")
    
    # pytestでテストを実行
    result = pytest.main([
        str(test_file),
        "-v",
        "--tb=short"
    ])
    
    if result == 0:
        print("✅ システムステータスページのテストが成功しました")
    else:
        print("❌ システムステータスページのテストが失敗しました")
    
    return result == 0

if __name__ == "__main__":
    success = run_system_status_tests()
    sys.exit(0 if success else 1) 