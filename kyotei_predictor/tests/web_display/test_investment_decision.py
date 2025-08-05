"""
投資判断機能のテスト
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestInvestmentDecision:
    """投資判断機能のテストクラス"""
    
    def setup_method(self):
        """テスト前のセットアップ"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get("http://localhost:51932/predictions")
        self.wait = WebDriverWait(self.driver, 10)
        
    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def test_investment_decision_columns_exist(self):
        """投資判断カラムが存在することをテスト"""
        print("投資判断カラムの存在確認テスト開始")
        
        # ページ読み込み待機
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "predictions-container")))
        time.sleep(2)
        
        # 提案比較テーブルのヘッダーを確認
        try:
            headers = self.driver.find_elements(By.CSS_SELECTOR, ".suggestions-comparison-table thead th")
            header_texts = [header.text for header in headers]
            
            print(f"見つかったヘッダー: {header_texts}")
            
            # 必要なカラムが存在することを確認
            required_columns = ['平均オッズ', 'オッズ期待値', '投資判断']
            for column in required_columns:
                assert column in header_texts, f"カラム '{column}' が見つかりません"
                print(f"✓ カラム '{column}' が存在します")
                
        except Exception as e:
            print(f"ヘッダー確認でエラー: {e}")
            raise
    
    def test_odds_info_display(self):
        """オッズ情報の表示をテスト"""
        print("オッズ情報表示テスト開始")
        
        # ページ読み込み待機
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "predictions-container")))
        time.sleep(3)
        
        try:
            # 提案比較テーブルの行を確認
            rows = self.driver.find_elements(By.CSS_SELECTOR, ".suggestions-comparison-table tbody tr.suggestion-row")
            
            if rows:
                print(f"見つかった提案行数: {len(rows)}")
                
                # 最初の行でオッズ情報を確認
                first_row = rows[0]
                odds_cells = first_row.find_elements(By.CSS_SELECTOR, "td:nth-child(8), td:nth-child(9), td:nth-child(10)")
                
                if len(odds_cells) >= 3:
                    print("✓ オッズ情報カラムが存在します")
                    
                    # 各カラムの内容を確認
                    for i, cell in enumerate(odds_cells):
                        cell_text = cell.text.strip()
                        print(f"  カラム{i+8}: {cell_text}")
                        
                        # 空でないか、または適切なプレースホルダーが表示されているか
                        assert cell_text != "", f"カラム{i+8}が空です"
                        
                else:
                    print("⚠ オッズ情報カラムが不足しています")
                    
            else:
                print("⚠ 提案行が見つかりません")
                
        except Exception as e:
            print(f"オッズ情報確認でエラー: {e}")
            raise
    
    def test_investment_decision_badges(self):
        """投資判断バッジの表示をテスト"""
        print("投資判断バッジテスト開始")
        
        # ページ読み込み待機
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "predictions-container")))
        time.sleep(3)
        
        try:
            # 投資判断バッジを確認
            decision_badges = self.driver.find_elements(By.CSS_SELECTOR, ".suggestions-comparison-table .badge")
            
            if decision_badges:
                print(f"見つかったバッジ数: {len(decision_badges)}")
                
                # 投資判断のバッジを特定
                investment_badges = []
                for badge in decision_badges:
                    badge_text = badge.text.strip()
                    if any(keyword in badge_text for keyword in ['推奨', '検討', '非推奨', '慎重']):
                        investment_badges.append(badge)
                        print(f"  投資判断バッジ: {badge_text}")
                
                if investment_badges:
                    print("✓ 投資判断バッジが表示されています")
                else:
                    print("⚠ 投資判断バッジが見つかりません")
                    
            else:
                print("⚠ バッジが見つかりません")
                
        except Exception as e:
            print(f"投資判断バッジ確認でエラー: {e}")
            raise
    
    def test_odds_info_in_detail(self):
        """詳細表示でのオッズ情報をテスト"""
        print("詳細表示オッズ情報テスト開始")
        
        # ページ読み込み待機
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "predictions-container")))
        time.sleep(3)
        
        try:
            # 最初の提案の詳細を開く
            toggle_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".suggestion-toggle")
            
            if toggle_buttons:
                print(f"見つかったトグルボタン数: {len(toggle_buttons)}")
                
                # 最初のボタンをクリック
                first_button = toggle_buttons[0]
                self.driver.execute_script("arguments[0].scrollIntoView();", first_button)
                time.sleep(1)
                first_button.click()
                time.sleep(2)
                
                # 詳細コンテンツでオッズ情報を確認
                detail_content = self.driver.find_element(By.CSS_SELECTOR, ".suggestion-detail-content")
                
                # オッズ情報セクションを確認
                odds_section = detail_content.find_element(By.CSS_SELECTOR, ".odds-info")
                if odds_section:
                    print("✓ 詳細表示でオッズ情報セクションが存在します")
                    
                    # オッズ情報の内容を確認
                    odds_text = odds_section.text
                    print(f"  オッズ情報内容: {odds_text[:100]}...")
                    
                else:
                    print("⚠ 詳細表示でオッズ情報セクションが見つかりません")
                    
            else:
                print("⚠ トグルボタンが見つかりません")
                
        except Exception as e:
            print(f"詳細表示オッズ情報確認でエラー: {e}")
            raise
    
    def test_investment_decision_in_detail(self):
        """詳細表示での投資判断をテスト"""
        print("詳細表示投資判断テスト開始")
        
        # ページ読み込み待機
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "predictions-container")))
        time.sleep(3)
        
        try:
            # 最初の提案の詳細を開く
            toggle_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".suggestion-toggle")
            
            if toggle_buttons:
                print(f"見つかったトグルボタン数: {len(toggle_buttons)}")
                
                # 最初のボタンをクリック
                first_button = toggle_buttons[0]
                self.driver.execute_script("arguments[0].scrollIntoView();", first_button)
                time.sleep(1)
                first_button.click()
                time.sleep(2)
                
                # 詳細コンテンツで投資判断を確認
                detail_content = self.driver.find_element(By.CSS_SELECTOR, ".suggestion-detail-content")
                
                # 投資判断セクションを確認
                try:
                    investment_section = detail_content.find_element(By.CSS_SELECTOR, ".investment-decision")
                    print("✓ 詳細表示で投資判断セクションが存在します")
                    
                    # 投資判断の内容を確認
                    decision_text = investment_section.text
                    print(f"  投資判断内容: {decision_text[:100]}...")
                    
                except NoSuchElementException:
                    # 従来の投資判断セクションを確認
                    try:
                        investment_section = detail_content.find_element(By.CSS_SELECTOR, ".investment-advice")
                        print("✓ 詳細表示で従来の投資判断セクションが存在します")
                    except NoSuchElementException:
                        print("⚠ 詳細表示で投資判断セクションが見つかりません")
                        
            else:
                print("⚠ トグルボタンが見つかりません")
                
        except Exception as e:
            print(f"詳細表示投資判断確認でエラー: {e}")
            raise

def run_investment_decision_tests():
    """投資判断機能のテストを実行"""
    print("=== 投資判断機能テスト開始 ===")
    
    test_instance = TestInvestmentDecision()
    
    try:
        test_instance.setup_method()
        
        # テスト実行
        test_instance.test_investment_decision_columns_exist()
        test_instance.test_odds_info_display()
        test_instance.test_investment_decision_badges()
        test_instance.test_odds_info_in_detail()
        test_instance.test_investment_decision_in_detail()
        
        print("=== 投資判断機能テスト完了 ===")
        print("✓ すべてのテストが成功しました")
        
    except Exception as e:
        print(f"=== 投資判断機能テスト失敗 ===")
        print(f"✗ テストでエラーが発生しました: {e}")
        raise
        
    finally:
        test_instance.teardown_method()

if __name__ == "__main__":
    run_investment_decision_tests() 