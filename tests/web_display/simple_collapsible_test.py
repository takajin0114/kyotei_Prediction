#!/usr/bin/env python3
"""
シンプルなセクション折り畳み機能テスト
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_collapsible_sections():
    """セクション折り畳み機能のテスト"""
    print("セクション折り畳み機能テスト開始")
    
    # Chromeオプション設定
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        # WebDriver初期化
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        # ページにアクセス
        print("ページにアクセス中...")
        driver.get("http://127.0.0.1:51932/predictions")
        time.sleep(3)  # ページ読み込み待機
        
        # セクションヘッダーを取得
        print("セクションヘッダーを検索中...")
        section_headers = driver.find_elements(By.CLASS_NAME, "section-header")
        print(f"セクションヘッダー数: {len(section_headers)}")
        
        if not section_headers:
            print("❌ セクションヘッダーが見つかりません")
            return False
        
        # 最初のセクションをテスト
        first_header = section_headers[0]
        race_id = first_header.get_attribute("data-race-id")
        section_type = first_header.get_attribute("data-section")
        
        print(f"テスト対象: {race_id}-{section_type}")
        
        # セクションコンテンツを取得（正しい要素）
        section_content = driver.find_element(By.CSS_SELECTOR, f"#section-{race_id}-{section_type} .section-content")
        
        # 初期状態を確認
        initial_class = section_content.get_attribute("class") or ""
        initial_display = section_content.value_of_css_property("display")
        initial_has_show = "show" in initial_class
        
        print(f"初期状態:")
        print(f"  クラス: {initial_class}")
        print(f"  display: {initial_display}")
        print(f"  showクラスあり: {initial_has_show}")
        
        # セクションヘッダーをクリック
        print("セクションヘッダーをクリック...")
        first_header.click()
        time.sleep(2)  # アニメーション待機
        
        # クリック後の状態を確認
        after_click_class = section_content.get_attribute("class") or ""
        after_click_display = section_content.value_of_css_property("display")
        after_click_has_show = "show" in after_click_class
        
        print(f"クリック後:")
        print(f"  クラス: {after_click_class}")
        print(f"  display: {after_click_display}")
        print(f"  showクラスあり: {after_click_has_show}")
        
        # 状態が変わったことを確認
        if initial_has_show == after_click_has_show:
            print("❌ セクションの状態が変わりませんでした")
            return False
        
        print("✅ セクションの状態が正常に変更されました")
        
        # 再度クリックして元の状態に戻す
        print("再度クリックして元の状態に戻す...")
        first_header.click()
        time.sleep(2)
        
        final_class = section_content.get_attribute("class") or ""
        final_display = section_content.value_of_css_property("display")
        final_has_show = "show" in final_class
        
        print(f"最終状態:")
        print(f"  クラス: {final_class}")
        print(f"  display: {final_display}")
        print(f"  showクラスあり: {final_has_show}")
        
        # 元の状態に戻ったことを確認
        if initial_has_show != final_has_show:
            print("❌ セクションが元の状態に戻りませんでした")
            return False
        
        print("✅ セクションが元の状態に正常に戻りました")
        print("🎉 セクション折り畳み機能テスト成功！")
        return True
        
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    success = test_collapsible_sections()
    exit(0 if success else 1) 