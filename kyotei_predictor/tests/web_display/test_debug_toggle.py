import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class TestDebugToggle:
    """トグルボタンのデバッグテスト"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Chromeドライバーの設定（ヘッドレスモードを無効化）"""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # デバッグのためヘッドレスモードを無効化
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_debug_toggle_functionality(self, driver):
        """トグルボタンの詳細デバッグテスト"""
        print("🔍 トグルボタンデバッグテスト開始...")
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
            print(f"🖱️ 最初のトグルボタン: {suggestion_id}")
            
            # 詳細行を確認
            detail_row = driver.find_element(By.ID, f"{suggestion_id}-detail")
            print(f"📊 詳細行要素: {detail_row}")
            print(f"📊 詳細行のHTML: {detail_row.get_attribute('outerHTML')[:200]}...")
            
            # 初期状態を確認
            initial_display = detail_row.value_of_css_property("display")
            initial_visibility = detail_row.value_of_css_property("visibility")
            initial_opacity = detail_row.value_of_css_property("opacity")
            print(f"📊 初期状態 - display: {initial_display}, visibility: {initial_visibility}, opacity: {initial_opacity}")
            
            # ボタンの状態を確認
            button_classes = first_button.get_attribute("class")
            icon_classes = first_button.find_element(By.TAG_NAME, "i").get_attribute("class")
            print(f"📊 ボタンクラス: {button_classes}")
            print(f"📊 アイコンクラス: {icon_classes}")
            
            # ボタンをクリック
            print("🖱️ ボタンをクリック中...")
            driver.execute_script("arguments[0].click();", first_button)
            time.sleep(3)
            
            # クリック後の状態を確認
            updated_display = detail_row.value_of_css_property("display")
            updated_visibility = detail_row.value_of_css_property("visibility")
            updated_opacity = detail_row.value_of_css_property("opacity")
            print(f"📊 クリック後 - display: {updated_display}, visibility: {updated_visibility}, opacity: {updated_opacity}")
            
            # ボタンの状態を再確認
            button_classes_after = first_button.get_attribute("class")
            icon_classes_after = first_button.find_element(By.TAG_NAME, "i").get_attribute("class")
            print(f"📊 クリック後ボタンクラス: {button_classes_after}")
            print(f"📊 クリック後アイコンクラス: {icon_classes_after}")
            
            # ブラウザのコンソールログを確認
            logs = driver.get_log('browser')
            print(f"📊 ブラウザログ数: {len(logs)}")
            for log in logs[-10:]:  # 最新の10件
                print(f"📊 ログ: {log}")
            
            # 手動でJavaScriptを実行してテスト
            print("🖱️ 手動でJavaScriptを実行...")
            result = driver.execute_script("""
                const detailRow = document.getElementById(arguments[0]);
                const currentDisplay = detailRow.style.display;
                detailRow.style.display = currentDisplay === 'none' ? 'table-row' : 'none';
                return {
                    before: currentDisplay,
                    after: detailRow.style.display,
                    element: detailRow.outerHTML.substring(0, 100)
                };
            """, f"{suggestion_id}-detail")
            print(f"📊 JavaScript実行結果: {result}")
            
            time.sleep(5)  # 結果を確認するための待機時間
        else:
            print("⚠️ トグルボタンが見つかりません")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 