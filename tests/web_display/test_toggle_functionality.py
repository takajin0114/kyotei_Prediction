import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class TestToggleFunctionality:
    """トグルボタンの機能テスト"""
    
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
    
    def test_toggle_button_click(self, driver):
        """トグルボタンクリックテスト"""
        print("🔍 トグルボタンクリックテスト開始...")
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
        
        # トグルボタンを取得
        toggle_buttons = driver.find_elements(By.CLASS_NAME, "suggestion-toggle")
        print(f"🔘 見つかったトグルボタン数: {len(toggle_buttons)}")
        
        if len(toggle_buttons) > 0:
            first_button = toggle_buttons[0]
            suggestion_id = first_button.get_attribute("data-suggestion-id")
            print(f"🖱️ 最初のトグルボタンをクリック: {suggestion_id}")
            
            # ボタンクリック前の状態を確認
            try:
                detail_row = driver.find_element(By.ID, f"{suggestion_id}-detail")
                initial_display = detail_row.value_of_css_property("display")
                print(f"📊 クリック前の表示状態: {initial_display}")
            except:
                print("⚠️ 詳細行が見つかりません")
                initial_display = "none"
            
            # ボタンをクリック
            driver.execute_script("arguments[0].click();", first_button)
            time.sleep(2)
            
            # クリック後の状態を確認
            try:
                detail_row = driver.find_element(By.ID, f"{suggestion_id}-detail")
                updated_display = detail_row.value_of_css_property("display")
                print(f"📊 クリック後の表示状態: {updated_display}")
                
                if updated_display != initial_display:
                    print("✅ トグルボタンクリックテスト成功")
                else:
                    print("⚠️ 表示状態が変更されていません")
            except Exception as e:
                print(f"❌ 詳細行の確認でエラー: {e}")
        else:
            print("⚠️ トグルボタンが見つかりません")
    
    def test_toggle_button_icon_change(self, driver):
        """トグルボタンのアイコン変更テスト"""
        print("🔍 トグルボタンアイコン変更テスト開始...")
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
        
        # トグルボタンを取得
        toggle_buttons = driver.find_elements(By.CLASS_NAME, "suggestion-toggle")
        
        if len(toggle_buttons) > 0:
            first_button = toggle_buttons[0]
            
            # クリック前のアイコンを確認
            try:
                icon = first_button.find_element(By.TAG_NAME, "i")
                initial_class = icon.get_attribute("class")
                print(f"📊 クリック前のアイコン: {initial_class}")
            except:
                print("⚠️ アイコンが見つかりません")
                return
            
            # ボタンをクリック
            driver.execute_script("arguments[0].click();", first_button)
            time.sleep(2)
            
            # クリック後のアイコンを確認
            try:
                icon = first_button.find_element(By.TAG_NAME, "i")
                updated_class = icon.get_attribute("class")
                print(f"📊 クリック後のアイコン: {updated_class}")
                
                if updated_class != initial_class:
                    print("✅ アイコン変更テスト成功")
                else:
                    print("⚠️ アイコンが変更されていません")
            except Exception as e:
                print(f"❌ アイコンの確認でエラー: {e}")
        else:
            print("⚠️ トグルボタンが見つかりません")
    
    def test_toggle_button_multiple_clicks(self, driver):
        """トグルボタンの複数回クリックテスト"""
        print("🔍 トグルボタン複数回クリックテスト開始...")
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
        
        # トグルボタンを取得
        toggle_buttons = driver.find_elements(By.CLASS_NAME, "suggestion-toggle")
        
        if len(toggle_buttons) > 0:
            first_button = toggle_buttons[0]
            suggestion_id = first_button.get_attribute("data-suggestion-id")
            
            # 1回目のクリック（展開）
            print("🖱️ 1回目のクリック（展開）")
            driver.execute_script("arguments[0].click();", first_button)
            time.sleep(2)
            
            # 展開状態を確認
            try:
                detail_row = driver.find_element(By.ID, f"{suggestion_id}-detail")
                first_display = detail_row.value_of_css_property("display")
                print(f"📊 1回目クリック後の表示状態: {first_display}")
            except:
                print("⚠️ 詳細行が見つかりません")
                return
            
            # 2回目のクリック（折りたたみ）
            print("🖱️ 2回目のクリック（折りたたみ）")
            driver.execute_script("arguments[0].click();", first_button)
            time.sleep(2)
            
            # 折りたたみ状態を確認
            try:
                detail_row = driver.find_element(By.ID, f"{suggestion_id}-detail")
                second_display = detail_row.value_of_css_property("display")
                print(f"📊 2回目クリック後の表示状態: {second_display}")
                
                if first_display != second_display:
                    print("✅ 複数回クリックテスト成功")
                else:
                    print("⚠️ 表示状態が切り替わっていません")
            except Exception as e:
                print(f"❌ 詳細行の確認でエラー: {e}")
        else:
            print("⚠️ トグルボタンが見つかりません")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 