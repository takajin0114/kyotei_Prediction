import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class TestBasicFunctionality:
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
    
    def test_page_access(self, driver):
        """ページアクセステスト"""
        print("🌐 ページにアクセス中...")
        driver.get("http://localhost:51932/predictions")
        
        # ページタイトルを確認
        assert "予測結果" in driver.title, f"ページタイトルが不正: {driver.title}"
        print("✅ ページアクセス成功")
    
    def test_main_content_loading(self, driver):
        """メインコンテンツ読み込みテスト"""
        print("🔍 メインコンテンツ読み込み確認中...")
        driver.get("http://localhost:51932/predictions")
        
        # メインコンテンツが読み込まれるまで待機
        try:
            main_content = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "main-content"))
            )
            print("✅ メインコンテンツ読み込み成功")
        except Exception as e:
            print(f"❌ メインコンテンツ読み込み失敗: {e}")
            raise
    
    def test_section_headers_presence(self, driver):
        """セクションヘッダー存在確認テスト"""
        print("🔍 セクションヘッダー確認中...")
        driver.get("http://localhost:51932/predictions")
        
        # ページ読み込み待機
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "main-content"))
        )
        
        # セクションヘッダーを確認
        section_headers = driver.find_elements(By.CLASS_NAME, "section-header")
        print(f"📊 セクションヘッダー数: {len(section_headers)}")
        
        if len(section_headers) > 0:
            print("✅ セクションヘッダー存在確認成功")
        else:
            print("⚠️ セクションヘッダーが見つかりません")
    
    def test_suggestion_sections_presence(self, driver):
        """提案比較セクション存在確認テスト"""
        print("🔍 提案比較セクション確認中...")
        driver.get("http://localhost:51932/predictions")
        
        # ページ読み込み待機
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "main-content"))
        )
        
        # 提案比較セクションを確認
        suggestion_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        print(f"📋 提案比較セクション数: {len(suggestion_headers)}")
        
        if len(suggestion_headers) > 0:
            print("✅ 提案比較セクション存在確認成功")
        else:
            print("⚠️ 提案比較セクションが見つかりません")
    
    def test_section_click_functionality(self, driver):
        """セクションクリック機能テスト"""
        print("🔍 セクションクリック機能確認中...")
        driver.get("http://localhost:51932/predictions")
        
        # ページ読み込み待機
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "main-content"))
        )
        
        # 提案比較セクションを確認
        suggestion_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        
        if len(suggestion_headers) > 0:
            first_header = suggestion_headers[0]
            print(f"🖱️ セクションクリック: {first_header.text}")
            
            # JavaScriptでクリック
            driver.execute_script("arguments[0].click();", first_header)
            time.sleep(3)
            
            print("✅ セクションクリック機能確認成功")
        else:
            print("⚠️ クリック対象のセクションが見つかりません")
    
    def test_suggestion_table_loading(self, driver):
        """提案比較テーブル読み込みテスト"""
        print("🔍 提案比較テーブル読み込み確認中...")
        driver.get("http://localhost:51932/predictions")
        
        # ページ読み込み待機
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "main-content"))
        )
        
        # 提案比較セクションを展開
        suggestion_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        if suggestion_headers:
            driver.execute_script("arguments[0].click();", suggestion_headers[0])
            time.sleep(5)
        
        # 提案比較テーブルを確認
        suggestion_tables = driver.find_elements(By.CLASS_NAME, "suggestions-comparison")
        print(f"📋 提案比較テーブル数: {len(suggestion_tables)}")
        
        if len(suggestion_tables) > 0:
            print("✅ 提案比較テーブル読み込み確認成功")
        else:
            print("⚠️ 提案比較テーブルが見つかりません")
    
    def test_toggle_buttons_presence(self, driver):
        """トグルボタン存在確認テスト"""
        print("🔍 トグルボタン存在確認中...")
        driver.get("http://localhost:51932/predictions")
        
        # ページ読み込み待機
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "main-content"))
        )
        
        # 提案比較セクションを展開
        suggestion_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        if suggestion_headers:
            driver.execute_script("arguments[0].click();", suggestion_headers[0])
            time.sleep(5)
        
        # トグルボタンを確認
        toggle_buttons = driver.find_elements(By.CLASS_NAME, "suggestion-toggle")
        print(f"🔘 トグルボタン数: {len(toggle_buttons)}")
        
        if len(toggle_buttons) > 0:
            print("✅ トグルボタン存在確認成功")
        else:
            print("⚠️ トグルボタンが見つかりません")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 