#!/usr/bin/env python3
"""
displayプロパティの変更を詳細にテスト
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def test_display_property():
    """displayプロパティの変更をテスト"""
    print("displayプロパティ変更テスト開始")
    
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
        
        # 初期状態を詳細確認
        initial_class = section_content.get_attribute("class") or ""
        initial_display = section_content.value_of_css_property("display")
        initial_has_show = "show" in initial_class
        
        print(f"=== 初期状態 ===")
        print(f"  クラス: {initial_class}")
        print(f"  display: {initial_display}")
        print(f"  showクラスあり: {initial_has_show}")
        print(f"  表示中: {initial_display != 'none'}")
        
        # セクションヘッダーをクリック
        print("セクションヘッダーをクリック...")
        first_header.click()
        time.sleep(2)  # アニメーション待機
        
        # クリック後の状態を詳細確認
        after_click_class = section_content.get_attribute("class") or ""
        after_click_display = section_content.value_of_css_property("display")
        after_click_has_show = "show" in after_click_class
        
        print(f"=== クリック後 ===")
        print(f"  クラス: {after_click_class}")
        print(f"  display: {after_click_display}")
        print(f"  showクラスあり: {after_click_has_show}")
        print(f"  表示中: {after_click_display != 'none'}")
        
        # displayプロパティが正しく変更されているか確認
        if initial_display == after_click_display:
            print("❌ displayプロパティが変更されていません")
            print(f"  期待値: none -> block")
            print(f"  実際値: {initial_display} -> {after_click_display}")
            return False
        
        # 正しい方向に変更されているか確認
        if initial_has_show and after_click_display != "none":
            print("❌ 展開状態から折り畳み状態に正しく変更されていません")
            return False
        
        if not initial_has_show and after_click_display != "block":
            print("❌ 折り畳み状態から展開状態に正しく変更されていません")
            return False
        
        print("✅ displayプロパティが正しく変更されました")
        
        # 再度クリックして元の状態に戻す
        print("再度クリックして元の状態に戻す...")
        first_header.click()
        time.sleep(2)
        
        final_class = section_content.get_attribute("class") or ""
        final_display = section_content.value_of_css_property("display")
        final_has_show = "show" in final_class
        
        print(f"=== 最終状態 ===")
        print(f"  クラス: {final_class}")
        print(f"  display: {final_display}")
        print(f"  showクラスあり: {final_has_show}")
        print(f"  表示中: {final_display != 'none'}")
        
        # 元の状態に戻ったことを確認
        if initial_display != final_display:
            print("❌ displayプロパティが元の状態に戻りませんでした")
            return False
        
        print("✅ displayプロパティが元の状態に正常に戻りました")
        print("🎉 displayプロパティ変更テスト成功！")
        return True
        
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    success = test_display_property()
    exit(0 if success else 1) 