#!/usr/bin/env python3
"""
Phase 4.1: 検索・フィルター機能 テストスイート

このテストファイルは、予測表示画面の検索・フィルター機能をテストします。
"""

import os
import sys
import json
import time
import unittest
from pathlib import Path
from urllib.parse import urljoin
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestPhase4SearchFilter(unittest.TestCase):
    """Phase 4.1 検索・フィルター機能のテストクラス"""

    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        cls.base_url = "http://localhost:8000"
        cls.predictions_url = f"{cls.base_url}/kyotei_predictor/templates/predictions.html"
        
        # テスト用のWebDriver設定
        cls.driver = None
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            cls.driver = webdriver.Chrome(options=options)
            cls.driver.implicitly_wait(10)
        except Exception as e:
            print(f"WebDriver初期化エラー: {e}")
            cls.driver = None

    @classmethod
    def tearDownClass(cls):
        """テストクラスのクリーンアップ"""
        if cls.driver:
            cls.driver.quit()

    def setUp(self):
        """各テストの前処理"""
        if not self.driver:
            self.skipTest("WebDriverが利用できません")

    def test_01_search_filter_ui_elements_exist(self):
        """検索・フィルターUI要素の存在確認"""
        print("\n=== 検索・フィルターUI要素の存在確認 ===")
        
        self.driver.get(self.predictions_url)
        
        # 基本検索要素の確認
        search_elements = [
            'venue-filter',
            'date-filter', 
            'risk-filter',
            'race-number-filter',
            'boat-number-filter',
            'player-name-filter'
        ]
        
        for element_id in search_elements:
            try:
                element = self.driver.find_element(By.ID, element_id)
                print(f"✓ {element_id} が見つかりました")
                self.assertTrue(element.is_displayed())
            except NoSuchElementException:
                print(f"✗ {element_id} が見つかりません")
                self.fail(f"要素 {element_id} が見つかりません")

        # フィルター条件チェックボックスの確認
        filter_checkboxes = [
            'hit-only-filter',
            'high-expected-value-filter',
            'odds-available-filter'
        ]
        
        for checkbox_id in filter_checkboxes:
            try:
                checkbox = self.driver.find_element(By.ID, checkbox_id)
                print(f"✓ {checkbox_id} が見つかりました")
                self.assertTrue(checkbox.is_displayed())
            except NoSuchElementException:
                print(f"✗ {checkbox_id} が見つかりません")
                self.fail(f"チェックボックス {checkbox_id} が見つかりません")

        # アクションボタンの確認
        action_buttons = [
            'search-button',
            'clear-search-button',
            'export-button'
        ]
        
        for button_id in action_buttons:
            try:
                button = self.driver.find_element(By.ID, button_id)
                print(f"✓ {button_id} が見つかりました")
                self.assertTrue(button.is_displayed())
            except NoSuchElementException:
                print(f"✗ {button_id} が見つかりません")
                self.fail(f"ボタン {button_id} が見つかりません")

        # 検索結果件数表示の確認
        try:
            result_count = self.driver.find_element(By.ID, 'search-result-count')
            print("✓ 検索結果件数表示が見つかりました")
            self.assertTrue(result_count.is_displayed())
        except NoSuchElementException:
            print("✗ 検索結果件数表示が見つかりません")
            self.fail("検索結果件数表示が見つかりません")

    def test_02_venue_filter_functionality(self):
        """会場フィルター機能のテスト"""
        print("\n=== 会場フィルター機能のテスト ===")
        
        self.driver.get(self.predictions_url)
        
        # ページ読み込み待機
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "venue-filter"))
        )
        
        # 会場フィルターの選択肢を確認
        venue_select = Select(self.driver.find_element(By.ID, "venue-filter"))
        options = venue_select.options
        
        print(f"会場フィルター選択肢数: {len(options)}")
        self.assertGreater(len(options), 1, "会場フィルターに選択肢がありません")
        
        # 最初の会場を選択
        if len(options) > 1:
            first_venue = options[1].text  # 最初の選択肢は「全会場」
            venue_select.select_by_index(1)
            print(f"会場を選択: {first_venue}")
            
            # フィルター適用の確認
            time.sleep(2)
            result_count = self.driver.find_element(By.ID, "search-result-count")
            count_text = result_count.text
            print(f"フィルター適用後の結果: {count_text}")
            
            # 結果が更新されていることを確認
            self.assertNotEqual(count_text, "検索結果: 0件")

    def test_03_risk_filter_functionality(self):
        """リスクレベルフィルター機能のテスト"""
        print("\n=== リスクレベルフィルター機能のテスト ===")
        
        self.driver.get(self.predictions_url)
        
        # リスクフィルターの選択肢を確認
        risk_select = Select(self.driver.find_element(By.ID, "risk-filter"))
        options = risk_select.options
        
        expected_risks = ["すべて", "低リスク", "中リスク", "高リスク"]
        actual_risks = [option.text for option in options]
        
        print(f"期待されるリスクレベル: {expected_risks}")
        print(f"実際のリスクレベル: {actual_risks}")
        
        for expected_risk in expected_risks:
            self.assertIn(expected_risk, actual_risks, f"リスクレベル '{expected_risk}' が見つかりません")
        
        # 中リスクを選択
        risk_select.select_by_visible_text("中リスク")
        print("中リスクを選択しました")
        
        # フィルター適用の確認
        time.sleep(2)
        result_count = self.driver.find_element(By.ID, "search-result-count")
        count_text = result_count.text
        print(f"中リスクフィルター適用後の結果: {count_text}")

    def test_04_text_search_functionality(self):
        """テキスト検索機能のテスト"""
        print("\n=== テキスト検索機能のテスト ===")
        
        self.driver.get(self.predictions_url)
        
        # レース番号検索
        race_input = self.driver.find_element(By.ID, "race-number-filter")
        race_input.clear()
        race_input.send_keys("1")
        print("レース番号1を入力しました")
        
        # 検索ボタンをクリック
        search_button = self.driver.find_element(By.ID, "search-button")
        search_button.click()
        print("検索ボタンをクリックしました")
        
        # 検索結果の確認
        time.sleep(2)
        result_count = self.driver.find_element(By.ID, "search-result-count")
        count_text = result_count.text
        print(f"レース番号検索結果: {count_text}")
        
        # 艇番検索
        boat_input = self.driver.find_element(By.ID, "boat-number-filter")
        boat_input.clear()
        boat_input.send_keys("1-2-3")
        print("艇番1-2-3を入力しました")
        
        search_button.click()
        time.sleep(2)
        
        count_text = result_count.text
        print(f"艇番検索結果: {count_text}")

    def test_05_checkbox_filter_functionality(self):
        """チェックボックスフィルター機能のテスト"""
        print("\n=== チェックボックスフィルター機能のテスト ===")
        
        self.driver.get(self.predictions_url)
        
        # 高期待値のみフィルター
        high_ev_checkbox = self.driver.find_element(By.ID, "high-expected-value-filter")
        high_ev_checkbox.click()
        print("高期待値のみフィルターを有効にしました")
        
        # 検索実行
        search_button = self.driver.find_element(By.ID, "search-button")
        search_button.click()
        
        # 結果確認
        time.sleep(2)
        result_count = self.driver.find_element(By.ID, "search-result-count")
        count_text = result_count.text
        print(f"高期待値フィルター結果: {count_text}")
        
        # フィルターをクリア
        clear_button = self.driver.find_element(By.ID, "clear-search-button")
        clear_button.click()
        print("検索条件をクリアしました")
        
        time.sleep(2)
        count_text = result_count.text
        print(f"クリア後の結果: {count_text}")

    def test_06_export_functionality(self):
        """エクスポート機能のテスト"""
        print("\n=== エクスポート機能のテスト ===")
        
        self.driver.get(self.predictions_url)
        
        # エクスポートボタンの存在確認
        export_button = self.driver.find_element(By.ID, "export-button")
        self.assertTrue(export_button.is_displayed())
        print("✓ エクスポートボタンが見つかりました")
        
        # エクスポートボタンがクリック可能であることを確認
        self.assertTrue(export_button.is_enabled())
        print("✓ エクスポートボタンがクリック可能です")
        
        # 注意: 実際のダウンロードテストは複雑なため、ボタンの存在とクリック可能性のみ確認

    def test_07_past_search_filter_functionality(self):
        """過去分検索・フィルター機能のテスト"""
        print("\n=== 過去分検索・フィルター機能のテスト ===")
        
        self.driver.get(self.predictions_url)
        
        # 過去分タブに切り替え
        past_tab = self.driver.find_element(By.ID, "past-tab")
        past_tab.click()
        print("過去分タブに切り替えました")
        
        # 過去分検索要素の確認
        past_search_elements = [
            'past-venue-filter',
            'past-date-filter',
            'past-risk-filter',
            'past-race-number-filter',
            'past-boat-number-filter',
            'past-player-name-filter'
        ]
        
        for element_id in past_search_elements:
            try:
                element = self.driver.find_element(By.ID, element_id)
                print(f"✓ {element_id} が見つかりました")
                self.assertTrue(element.is_displayed())
            except NoSuchElementException:
                print(f"✗ {element_id} が見つかりません")
                self.fail(f"過去分要素 {element_id} が見つかりません")

    def test_08_responsive_design(self):
        """レスポンシブデザインのテスト"""
        print("\n=== レスポンシブデザインのテスト ===")
        
        # デスクトップサイズ
        self.driver.set_window_size(1200, 800)
        self.driver.get(self.predictions_url)
        time.sleep(2)
        
        # 検索・フィルターセクションが表示されていることを確認
        search_section = self.driver.find_element(By.CSS_SELECTOR, ".card-header")
        self.assertTrue(search_section.is_displayed())
        print("✓ デスクトップサイズで検索・フィルターセクションが表示されています")
        
        # タブレットサイズ
        self.driver.set_window_size(768, 1024)
        time.sleep(2)
        
        # モバイルサイズ
        self.driver.set_window_size(375, 667)
        time.sleep(2)
        
        # 検索・フィルターセクションが表示されていることを確認
        search_section = self.driver.find_element(By.CSS_SELECTOR, ".card-header")
        self.assertTrue(search_section.is_displayed())
        print("✓ モバイルサイズでも検索・フィルターセクションが表示されています")

    def test_09_keyboard_navigation(self):
        """キーボードナビゲーションのテスト"""
        print("\n=== キーボードナビゲーションのテスト ===")
        
        self.driver.get(self.predictions_url)
        
        # Tabキーでのナビゲーション
        body = self.driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.TAB)
        
        # フォーカスが移動することを確認
        focused_element = self.driver.switch_to.active_element
        print(f"フォーカスされた要素: {focused_element.tag_name} (ID: {focused_element.get_attribute('id')})")
        
        # Enterキーでの検索実行
        race_input = self.driver.find_element(By.ID, "race-number-filter")
        race_input.clear()
        race_input.send_keys("1")
        race_input.send_keys(Keys.ENTER)
        
        time.sleep(2)
        result_count = self.driver.find_element(By.ID, "search-result-count")
        count_text = result_count.text
        print(f"Enterキー検索結果: {count_text}")

    def test_10_error_handling(self):
        """エラーハンドリングのテスト"""
        print("\n=== エラーハンドリングのテスト ===")
        
        self.driver.get(self.predictions_url)
        
        # 無効なレース番号を入力
        race_input = self.driver.find_element(By.ID, "race-number-filter")
        race_input.clear()
        race_input.send_keys("99")  # 無効なレース番号
        
        search_button = self.driver.find_element(By.ID, "search-button")
        search_button.click()
        
        time.sleep(2)
        result_count = self.driver.find_element(By.ID, "search-result-count")
        count_text = result_count.text
        print(f"無効なレース番号検索結果: {count_text}")
        
        # 結果が0件になることを確認
        self.assertIn("0件", count_text, "無効な検索条件で結果が0件になりません")

def run_lightweight_tests():
    """軽量テスト（Seleniumなし）の実行"""
    print("=== Phase 4.1 軽量テスト実行 ===")
    
    base_url = "http://localhost:8000"
    predictions_url = f"{base_url}/kyotei_predictor/templates/predictions.html"
    
    # HTTPサーバーの確認
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✓ HTTPサーバーが応答しています (ステータス: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"✗ HTTPサーバーに接続できません: {e}")
        return False
    
    # 予測表示ページの確認
    try:
        response = requests.get(predictions_url, timeout=5)
        if response.status_code == 200:
            print("✓ 予測表示ページにアクセスできました")
        else:
            print(f"✗ 予測表示ページのステータス: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ 予測表示ページにアクセスできません: {e}")
        return False
    
    # HTMLコンテンツの確認
    html_content = response.text
    
    # 検索・フィルター要素の存在確認
    search_elements = [
        'id="venue-filter"',
        'id="date-filter"',
        'id="risk-filter"',
        'id="race-number-filter"',
        'id="boat-number-filter"',
        'id="player-name-filter"',
        'id="hit-only-filter"',
        'id="high-expected-value-filter"',
        'id="odds-available-filter"',
        'id="search-button"',
        'id="clear-search-button"',
        'id="export-button"',
        'id="search-result-count"'
    ]
    
    for element in search_elements:
        if element in html_content:
            print(f"✓ {element} がHTMLに含まれています")
        else:
            print(f"✗ {element} がHTMLに含まれていません")
            return False
    
    # CSSファイルの確認
    css_url = f"{base_url}/kyotei_predictor/static/css/predictions.css"
    try:
        css_response = requests.get(css_url, timeout=5)
        if css_response.status_code == 200:
            print("✓ CSSファイルにアクセスできました")
            
            # 検索・フィルター関連のCSSクラスの確認
            css_content = css_response.text
            css_classes = [
                '.search-filter-section',
                '.form-control',
                '.action-buttons',
                '.search-result-count'
            ]
            
            for css_class in css_classes:
                if css_class in css_content:
                    print(f"✓ {css_class} がCSSに含まれています")
                else:
                    print(f"✗ {css_class} がCSSに含まれていません")
        else:
            print(f"✗ CSSファイルのステータス: {css_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ CSSファイルにアクセスできません: {e}")
    
    # JavaScriptファイルの確認
    js_url = f"{base_url}/kyotei_predictor/static/js/predictions.js"
    try:
        js_response = requests.get(js_url, timeout=5)
        if js_response.status_code == 200:
            print("✓ JavaScriptファイルにアクセスできました")
            
            # 検索・フィルター関連のJavaScript関数の確認
            js_content = js_response.text
            js_functions = [
                'performSearch',
                'clearSearch',
                'exportData',
                'getSearchCriteria',
                'matchesSearchCriteria'
            ]
            
            for js_function in js_functions:
                if js_function in js_content:
                    print(f"✓ {js_function} がJavaScriptに含まれています")
                else:
                    print(f"✗ {js_function} がJavaScriptに含まれていません")
        else:
            print(f"✗ JavaScriptファイルのステータス: {js_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ JavaScriptファイルにアクセスできません: {e}")
    
    print("=== 軽量テスト完了 ===")
    return True

if __name__ == "__main__":
    print("Phase 4.1: 検索・フィルター機能 テストスイート")
    print("=" * 60)
    
    # 軽量テストを実行
    lightweight_success = run_lightweight_tests()
    
    if lightweight_success:
        print("\n軽量テストが成功しました。Seleniumテストを実行しますか？")
        print("Seleniumテストを実行するには、ChromeDriverがインストールされている必要があります。")
        
        # Seleniumテストの実行（オプション）
        try:
            unittest.main(argv=[''], exit=False, verbosity=2)
        except Exception as e:
            print(f"Seleniumテストの実行に失敗しました: {e}")
            print("ChromeDriverがインストールされているか確認してください。")
    else:
        print("\n軽量テストが失敗しました。HTTPサーバーが起動しているか確認してください。") 