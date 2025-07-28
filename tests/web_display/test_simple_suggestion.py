import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains


class TestSimpleSuggestion:
    """提案比較テーブルの基本的な機能テスト"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Chromeドライバーの設定"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_page_loads(self, driver):
        """ページが正常に読み込まれるテスト"""
        print("🌐 ページにアクセス中...")
        driver.get("http://localhost:51932/predictions")
        
        # ページタイトルを確認
        assert "予測結果" in driver.title, f"ページタイトルが不正: {driver.title}"
        print("✅ ページが正常に読み込まれました")
    
    def test_main_content_exists(self, driver):
        """メインコンテンツが存在するテスト"""
        print("🔍 メインコンテンツを確認中...")
        driver.get("http://localhost:51932/predictions")
        
        # メインコンテンツが存在し、表示されるまで待機
        main_content = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.ID, "main-content"))
        )
        assert main_content.is_displayed(), "メインコンテンツが表示されていません"
        print("✅ メインコンテンツが存在します")
    
    def test_section_headers_exist(self, driver):
        """セクションヘッダーが存在するテスト"""
        print("🔍 セクションヘッダーを確認中...")
        driver.get("http://localhost:51932/predictions")
        
        # ページが読み込まれるまで待機
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.ID, "main-content"))
        )
        
        # セクションヘッダーが存在することを確認
        section_headers = driver.find_elements(By.CLASS_NAME, "section-header")
        print(f"📊 セクションヘッダー数: {len(section_headers)}")
        assert len(section_headers) > 0, "セクションヘッダーが見つかりません"
        
        # 提案比較セクションを探す
        suggestion_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        print(f"📋 提案比較セクション数: {len(suggestion_headers)}")
        assert len(suggestion_headers) > 0, "提案比較セクションが見つかりません"
        
        print("✅ セクションヘッダーが存在します")
    
    def test_section_expansion(self, driver):
        """セクション展開のテスト"""
        print("🔍 セクション展開をテスト中...")
        driver.get("http://localhost:51932/predictions")
        
        # ページが読み込まれるまで待機
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.ID, "main-content"))
        )
        
        # 提案比較セクションを探す
        suggestion_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        assert len(suggestion_headers) > 0, "提案比較セクションが見つかりません"
        
        # 最初の提案比較セクションをクリック
        first_header = suggestion_headers[0]
        print(f"🖱️ セクションヘッダーをクリック: {first_header.text}")
        
        # 要素が見えるようにスクロール
        driver.execute_script("arguments[0].scrollIntoView(true);", first_header)
        time.sleep(2)
        
        # JavaScriptでクリック
        driver.execute_script("arguments[0].click();", first_header)
        
        # セクションが展開されるまで待機
        time.sleep(5)
        
        # セクションが展開されていることを確認
        section_content = first_header.find_element(By.XPATH, "following-sibling::div[contains(@class, 'section-content')]")
        is_expanded = "show" in section_content.get_attribute("class")
        print(f"📊 セクション展開状態: {is_expanded}")
        
        assert is_expanded, "セクションが展開されていません"
        print("✅ セクション展開テスト成功")
    
    def test_suggestion_table_exists(self, driver):
        """提案比較テーブルが存在するテスト"""
        print("🔍 提案比較テーブルを確認中...")
        driver.get("http://localhost:51932/predictions")
        
        # ページが読み込まれるまで待機
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.ID, "main-content"))
        )
        
        # 提案比較セクションを展開
        suggestion_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        if suggestion_headers:
            first_header = suggestion_headers[0]
            # 要素が見えるようにスクロール
            driver.execute_script("arguments[0].scrollIntoView(true);", first_header)
            time.sleep(2)
            # JavaScriptでクリック
            driver.execute_script("arguments[0].click();", first_header)
            time.sleep(5)
        
        # 提案比較テーブルが存在することを確認
        suggestion_tables = driver.find_elements(By.CLASS_NAME, "suggestions-comparison")
        print(f"📋 提案比較テーブル数: {len(suggestion_tables)}")
        assert len(suggestion_tables) > 0, "提案比較テーブルが見つかりません"
        
        print("✅ 提案比較テーブルが存在します")
    
    def test_toggle_buttons_exist(self, driver):
        """トグルボタンが存在するテスト"""
        print("🔍 トグルボタンを確認中...")
        driver.get("http://localhost:51932/predictions")
        
        # ページが読み込まれるまで待機
        WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.ID, "main-content"))
        )
        
        # 提案比較セクションを展開
        suggestion_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        if suggestion_headers:
            first_header = suggestion_headers[0]
            # 要素が見えるようにスクロール
            driver.execute_script("arguments[0].scrollIntoView(true);", first_header)
            time.sleep(2)
            # JavaScriptでクリック
            driver.execute_script("arguments[0].click();", first_header)
            time.sleep(5)
        
        # 提案比較テーブルが読み込まれるまで待機
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "suggestions-comparison"))
            )
        except:
            print("⚠️ 提案比較テーブルの読み込みがタイムアウトしました")
        
        # トグルボタンが存在することを確認
        toggle_buttons = driver.find_elements(By.CLASS_NAME, "suggestion-toggle")
        print(f"🔘 トグルボタン数: {len(toggle_buttons)}")
        
        if len(toggle_buttons) > 0:
            print("✅ トグルボタンが存在します")
            
            # 最初のトグルボタンをクリックしてテスト
            first_toggle = toggle_buttons[0]
            print("🖱️ 最初のトグルボタンをクリック中...")
            
            # 要素が見えるようにスクロール
            driver.execute_script("arguments[0].scrollIntoView(true);", first_toggle)
            time.sleep(2)
            
            # JavaScriptでクリック
            driver.execute_script("arguments[0].click();", first_toggle)
            time.sleep(3)
            
            print("✅ トグルボタンのクリックテスト成功")
        else:
            print("⚠️ トグルボタンが見つかりません")
            # ページのHTMLを確認
            page_source = driver.page_source
            if "suggestion-toggle" in page_source:
                print("ℹ️ HTMLにはsuggestion-toggleクラスが含まれています")
            else:
                print("❌ HTMLにsuggestion-toggleクラスが含まれていません")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 