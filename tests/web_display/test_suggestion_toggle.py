import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestSuggestionToggle:
    """提案比較テーブルの各提案詳細の展開/折りたたみ機能テスト"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Chromeドライバーの設定"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # ヘッドレスモード
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    @pytest.fixture(scope="class")
    def setup_page(self, driver):
        """テストページのセットアップ"""
        # ローカルサーバーにアクセス
        driver.get("http://localhost:51932/predictions")
        
        # ページが完全に読み込まれるまで待機
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "main-content"))
        )
        
        # 提案比較テーブルが読み込まれるまで待機
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "suggestions-comparison"))
        )
        
        return driver
    
    def test_suggestion_section_expansion(self, setup_page):
        """提案比較セクションの展開テスト"""
        driver = setup_page
        
        # 提案比較セクションのヘッダーをクリック
        section_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        assert len(section_headers) > 0, "提案比較セクションが見つかりません"
        
        # 最初の提案比較セクションを展開
        first_header = section_headers[0]
        first_header.click()
        
        # セクションが展開されるまで待機
        time.sleep(2)
        
        # セクションが展開されていることを確認
        section_content = first_header.find_element(By.XPATH, "following-sibling::div[contains(@class, 'section-content')]")
        assert "show" in section_content.get_attribute("class"), "セクションが展開されていません"
        
        print("✅ 提案比較セクションの展開テスト成功")
    
    def test_suggestion_toggle_buttons_exist(self, setup_page):
        """提案トグルボタンの存在確認テスト"""
        driver = setup_page
        
        # 提案比較セクションを展開
        section_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        if section_headers:
            section_headers[0].click()
            time.sleep(2)
        
        # 提案トグルボタンが存在することを確認
        toggle_buttons = driver.find_elements(By.CLASS_NAME, "suggestion-toggle")
        assert len(toggle_buttons) > 0, "提案トグルボタンが見つかりません"
        
        print(f"✅ 提案トグルボタン {len(toggle_buttons)} 個を発見")
    
    def test_suggestion_detail_expansion(self, setup_page):
        """提案詳細の展開テスト"""
        driver = setup_page
        
        # 提案比較セクションを展開
        section_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        if section_headers:
            section_headers[0].click()
            time.sleep(2)
        
        # 提案トグルボタンを取得
        toggle_buttons = driver.find_elements(By.CLASS_NAME, "suggestion-toggle")
        assert len(toggle_buttons) > 0, "提案トグルボタンが見つかりません"
        
        # 最初の提案トグルボタンをクリック
        first_button = toggle_buttons[0]
        suggestion_id = first_button.get_attribute("data-suggestion-id")
        
        # ボタンクリック前の状態を確認
        detail_row = driver.find_element(By.ID, f"{suggestion_id}-detail")
        initial_display = detail_row.value_of_css_property("display")
        
        # ボタンをクリック
        first_button.click()
        time.sleep(1)
        
        # 詳細が展開されていることを確認
        updated_display = detail_row.value_of_css_property("display")
        assert updated_display != initial_display, "提案詳細の表示状態が変更されていません"
        
        # アイコンが変更されていることを確認
        icon = first_button.find_element(By.TAG_NAME, "i")
        assert "fa-chevron-up" in icon.get_attribute("class"), "アイコンが上向きに変更されていません"
        
        print("✅ 提案詳細の展開テスト成功")
    
    def test_suggestion_detail_collapse(self, setup_page):
        """提案詳細の折りたたみテスト"""
        driver = setup_page
        
        # 提案比較セクションを展開
        section_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        if section_headers:
            section_headers[0].click()
            time.sleep(2)
        
        # 提案トグルボタンを取得
        toggle_buttons = driver.find_elements(By.CLASS_NAME, "suggestion-toggle")
        assert len(toggle_buttons) > 0, "提案トグルボタンが見つかりません"
        
        # 最初の提案トグルボタンをクリックして展開
        first_button = toggle_buttons[0]
        suggestion_id = first_button.get_attribute("data-suggestion-id")
        first_button.click()
        time.sleep(1)
        
        # 再度クリックして折りたたみ
        first_button.click()
        time.sleep(1)
        
        # 詳細が折りたたまれていることを確認
        detail_row = driver.find_element(By.ID, f"{suggestion_id}-detail")
        display_state = detail_row.value_of_css_property("display")
        assert display_state == "none", "提案詳細が折りたたまれていません"
        
        # アイコンが元に戻っていることを確認
        icon = first_button.find_element(By.TAG_NAME, "i")
        assert "fa-chevron-down" in icon.get_attribute("class"), "アイコンが下向きに戻っていません"
        
        print("✅ 提案詳細の折りたたみテスト成功")
    
    def test_multiple_suggestions_toggle(self, setup_page):
        """複数の提案の展開/折りたたみテスト"""
        driver = setup_page
        
        # 提案比較セクションを展開
        section_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        if section_headers:
            section_headers[0].click()
            time.sleep(2)
        
        # 提案トグルボタンを取得
        toggle_buttons = driver.find_elements(By.CLASS_NAME, "suggestion-toggle")
        assert len(toggle_buttons) >= 2, "テストに必要な提案トグルボタンが不足しています"
        
        # 最初の2つの提案を展開
        for i in range(2):
            button = toggle_buttons[i]
            suggestion_id = button.get_attribute("data-suggestion-id")
            
            # 展開
            button.click()
            time.sleep(1)
            
            # 展開されていることを確認
            detail_row = driver.find_element(By.ID, f"{suggestion_id}-detail")
            display_state = detail_row.value_of_css_property("display")
            assert display_state != "none", f"提案 {i+1} が展開されていません"
            
            # アイコンを確認
            icon = button.find_element(By.TAG_NAME, "i")
            assert "fa-chevron-up" in icon.get_attribute("class"), f"提案 {i+1} のアイコンが上向きになっていません"
        
        # 最初の提案を折りたたみ
        first_button = toggle_buttons[0]
        first_suggestion_id = first_button.get_attribute("data-suggestion-id")
        first_button.click()
        time.sleep(1)
        
        # 最初の提案が折りたたまれていることを確認
        first_detail_row = driver.find_element(By.ID, f"{first_suggestion_id}-detail")
        first_display_state = first_detail_row.value_of_css_property("display")
        assert first_display_state == "none", "最初の提案が折りたたまれていません"
        
        # 2番目の提案は展開されたままであることを確認
        second_button = toggle_buttons[1]
        second_suggestion_id = second_button.get_attribute("data-suggestion-id")
        second_detail_row = driver.find_element(By.ID, f"{second_suggestion_id}-detail")
        second_display_state = second_detail_row.value_of_css_property("display")
        assert second_display_state != "none", "2番目の提案が折りたたまれています"
        
        print("✅ 複数の提案の展開/折りたたみテスト成功")
    
    def test_suggestion_detail_content(self, setup_page):
        """提案詳細の内容確認テスト"""
        driver = setup_page
        
        # 提案比較セクションを展開
        section_headers = driver.find_elements(By.CSS_SELECTOR, '.section-header[data-section="suggestions"]')
        if section_headers:
            section_headers[0].click()
            time.sleep(2)
        
        # 提案トグルボタンを取得
        toggle_buttons = driver.find_elements(By.CLASS_NAME, "suggestion-toggle")
        assert len(toggle_buttons) > 0, "提案トグルボタンが見つかりません"
        
        # 最初の提案を展開
        first_button = toggle_buttons[0]
        suggestion_id = first_button.get_attribute("data-suggestion-id")
        first_button.click()
        time.sleep(1)
        
        # 詳細内容が表示されていることを確認
        detail_row = driver.find_element(By.ID, f"{suggestion_id}-detail")
        detail_content = detail_row.find_element(By.CLASS_NAME, "suggestion-detail-content")
        
        # 詳細内容に必要な要素が含まれていることを確認
        assert detail_content.text.strip() != "", "提案詳細の内容が空です"
        
        # 組み合わせリストが表示されていることを確認
        try:
            combinations = detail_content.find_elements(By.CSS_SELECTOR, ".combination-badge")
            assert len(combinations) > 0, "組み合わせリストが表示されていません"
        except NoSuchElementException:
            # 組み合わせリストがない場合でも、何らかの内容があることを確認
            assert len(detail_content.text) > 10, "提案詳細に十分な内容がありません"
        
        print("✅ 提案詳細の内容確認テスト成功")


if __name__ == "__main__":
    # テストの実行
    pytest.main([__file__, "-v"]) 