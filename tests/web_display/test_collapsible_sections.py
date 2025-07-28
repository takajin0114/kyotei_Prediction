import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestCollapsibleSections(unittest.TestCase):
    """セクションの折り畳み機能のテスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        # Chromeオプション設定
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # ヘッドレスモード
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)
        
        # テスト用URL
        cls.base_url = "http://127.0.0.1:51932"
        
    @classmethod
    def tearDownClass(cls):
        """テストクラスのクリーンアップ"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def setUp(self):
        """各テストの前処理"""
        self.driver.get(f"{self.base_url}/predictions")
        time.sleep(2)  # ページ読み込み待機
    
    def test_section_headers_exist(self):
        """セクションヘッダーが存在することを確認"""
        print("テスト: セクションヘッダーの存在確認")
        
        # セクションヘッダーが表示されるまで待機
        try:
            section_headers = self.wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "section-header"))
            )
            print(f"セクションヘッダー数: {len(section_headers)}")
            self.assertGreater(len(section_headers), 0, "セクションヘッダーが見つかりません")
        except TimeoutException:
            self.fail("セクションヘッダーがタイムアウトしました")
    
    def test_section_content_initial_state(self):
        """セクションコンテンツの初期状態を確認"""
        print("テスト: セクションコンテンツの初期状態確認")
        
        # セクションコンテンツを取得
        section_contents = self.driver.find_elements(By.CLASS_NAME, "section-content")
        print(f"セクションコンテンツ数: {len(section_contents)}")
        
        for i, content in enumerate(section_contents):
            # 初期状態ではshowクラスが付いているはず
            class_attr = content.get_attribute("class") or ""
            has_show_class = "show" in class_attr
            display_style = content.value_of_css_property("display")
            print(f"セクション{i+1}: showクラス={has_show_class}, display={display_style}")
            
            # 初期状態では表示されているはず
            self.assertTrue(has_show_class, f"セクション{i+1}にshowクラスがありません")
            self.assertNotEqual(display_style, "none", f"セクション{i+1}が非表示になっています")
    
    def test_section_toggle_functionality(self):
        """セクションの折り畳み機能をテスト"""
        print("テスト: セクションの折り畳み機能")
        
        # 最初のセクションヘッダーを取得
        section_headers = self.driver.find_elements(By.CLASS_NAME, "section-header")
        if not section_headers:
            self.skipTest("セクションヘッダーが見つかりません")
        
        first_header = section_headers[0]
        race_id = first_header.get_attribute("data-race-id")
        section_type = first_header.get_attribute("data-section")
        
        print(f"テスト対象: {race_id}-{section_type}")
        
        # 対応するセクションコンテンツを取得
        section_content = self.driver.find_element(By.ID, f"section-{race_id}-{section_type}")
        
        # 初期状態を確認
        initial_class_attr = section_content.get_attribute("class") or ""
        initial_has_show = "show" in initial_class_attr
        initial_display = section_content.value_of_css_property("display")
        print(f"初期状態: showクラス={initial_has_show}, display={initial_display}")
        
        # セクションヘッダーをクリック
        print("セクションヘッダーをクリック...")
        first_header.click()
        time.sleep(1)  # アニメーション待機
        
        # クリック後の状態を確認
        after_click_class_attr = section_content.get_attribute("class") or ""
        after_click_has_show = "show" in after_click_class_attr
        after_click_display = section_content.value_of_css_property("display")
        print(f"クリック後: showクラス={after_click_has_show}, display={after_click_display}")
        
        # 状態が変わったことを確認
        self.assertNotEqual(initial_has_show, after_click_has_show, "セクションの状態が変わりませんでした")
        
        # 再度クリックして元の状態に戻す
        print("再度クリックして元の状態に戻す...")
        first_header.click()
        time.sleep(1)
        
        final_class_attr = section_content.get_attribute("class") or ""
        final_has_show = "show" in final_class_attr
        final_display = section_content.value_of_css_property("display")
        print(f"最終状態: showクラス={final_has_show}, display={final_display}")
        
        # 元の状態に戻ったことを確認
        self.assertEqual(initial_has_show, final_has_show, "セクションが元の状態に戻りませんでした")
    
    def test_all_sections_toggle(self):
        """全てのセクションの折り畳みをテスト"""
        print("テスト: 全てのセクションの折り畳み")
        
        section_headers = self.driver.find_elements(By.CLASS_NAME, "section-header")
        print(f"テスト対象セクション数: {len(section_headers)}")
        
        for i, header in enumerate(section_headers[:3]):  # 最初の3つだけテスト
            race_id = header.get_attribute("data-race-id")
            section_type = header.get_attribute("data-section")
            
            print(f"セクション{i+1}: {race_id}-{section_type}")
            
            # セクションコンテンツを取得
            try:
                section_content = self.driver.find_element(By.ID, f"section-{race_id}-{section_type}")
            except NoSuchElementException:
                print(f"セクションコンテンツが見つかりません: section-{race_id}-{section_type}")
                continue
            
            # 初期状態
            initial_class_attr = section_content.get_attribute("class") or ""
            initial_has_show = "show" in initial_class_attr
            
            # クリック
            header.click()
            time.sleep(0.5)
            
            # 状態確認
            after_click_class_attr = section_content.get_attribute("class") or ""
            after_click_has_show = "show" in after_click_class_attr
            print(f"  初期: {initial_has_show} -> クリック後: {after_click_has_show}")
            
            # 状態が変わったことを確認
            self.assertNotEqual(initial_has_show, after_click_has_show, 
                              f"セクション{i+1}の状態が変わりませんでした")
    
    def test_section_visibility_after_toggle(self):
        """セクションの可視性を詳細にテスト"""
        print("テスト: セクションの可視性詳細確認")
        
        section_headers = self.driver.find_elements(By.CLASS_NAME, "section-header")
        if not section_headers:
            self.skipTest("セクションヘッダーが見つかりません")
        
        first_header = section_headers[0]
        race_id = first_header.get_attribute("data-race-id")
        section_type = first_header.get_attribute("data-section")
        section_content = self.driver.find_element(By.ID, f"section-{race_id}-{section_type}")
        
        # 初期状態の詳細確認
        print("=== 初期状態 ===")
        self._print_section_state(section_content, "初期")
        
        # 折り畳み
        print("=== 折り畳み実行 ===")
        first_header.click()
        time.sleep(1)
        self._print_section_state(section_content, "折り畳み後")
        
        # 展開
        print("=== 展開実行 ===")
        first_header.click()
        time.sleep(1)
        self._print_section_state(section_content, "展開後")
    
    def _print_section_state(self, section_content, state_name):
        """セクションの状態を詳細に出力"""
        classes = section_content.get_attribute("class") or ""
        display = section_content.value_of_css_property("display")
        visibility = section_content.value_of_css_property("visibility")
        opacity = section_content.value_of_css_property("opacity")
        height = section_content.value_of_css_property("height")
        max_height = section_content.value_of_css_property("max-height")
        
        print(f"{state_name}:")
        print(f"  クラス: {classes}")
        print(f"  display: {display}")
        print(f"  visibility: {visibility}")
        print(f"  opacity: {opacity}")
        print(f"  height: {height}")
        print(f"  max-height: {max_height}")
        print(f"  showクラスあり: {'show' in classes}")
        print(f"  表示中: {display != 'none'}")


if __name__ == "__main__":
    # テスト実行
    unittest.main(verbosity=2) 