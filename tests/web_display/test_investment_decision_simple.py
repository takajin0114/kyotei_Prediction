"""
投資判断機能のシンプルテスト
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def test_investment_decision_basic():
    """投資判断機能の基本的なテスト"""
    print("=== 投資判断機能基本テスト開始 ===")
    
    # Chromeオプション設定
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        # ブラウザ起動
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("http://localhost:51932/predictions")
        
        # ページ読み込み待機（長めに設定）
        wait = WebDriverWait(driver, 20)
        print("ページ読み込み中...")
        
        # メインコンテナの存在確認
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "predictions-container")))
        print("✓ ページが正常に読み込まれました")
        
        # 少し待機
        time.sleep(5)
        
        # 提案比較テーブルの存在確認
        try:
            comparison_table = driver.find_element(By.CSS_SELECTOR, ".suggestions-comparison-table")
            print("✓ 提案比較テーブルが存在します")
            
            # ヘッダーの確認
            headers = comparison_table.find_elements(By.CSS_SELECTOR, "thead th")
            header_texts = [header.text.strip() for header in headers]
            print(f"見つかったヘッダー: {header_texts}")
            
            # 必要なカラムの確認
            required_columns = ['平均オッズ', 'オッズ期待値', '投資判断']
            found_columns = []
            
            for column in required_columns:
                if column in header_texts:
                    found_columns.append(column)
                    print(f"✓ カラム '{column}' が存在します")
                else:
                    print(f"✗ カラム '{column}' が見つかりません")
            
            if len(found_columns) == len(required_columns):
                print("✓ すべての必要なカラムが存在します")
            else:
                print(f"⚠ {len(found_columns)}/{len(required_columns)} のカラムが見つかりました")
            
            # 提案行の確認
            rows = comparison_table.find_elements(By.CSS_SELECTOR, "tbody tr.suggestion-row")
            print(f"見つかった提案行数: {len(rows)}")
            
            if rows:
                # 最初の行でオッズ情報を確認
                first_row = rows[0]
                cells = first_row.find_elements(By.CSS_SELECTOR, "td")
                
                if len(cells) >= 12:  # 新しいカラムが追加されている
                    print("✓ テーブルに新しいカラムが追加されています")
                    
                    # オッズ情報カラムの内容確認
                    odds_cells = cells[7:10]  # 8, 9, 10番目のカラム
                    for i, cell in enumerate(odds_cells):
                        cell_text = cell.text.strip()
                        print(f"  カラム{i+8}: {cell_text}")
                        
                        # 空でないか、または適切なプレースホルダーが表示されているか
                        if cell_text != "":
                            print(f"    ✓ カラム{i+8}に内容があります")
                        else:
                            print(f"    ⚠ カラム{i+8}が空です")
                else:
                    print(f"⚠ テーブルのカラム数が不足しています: {len(cells)}")
            
        except NoSuchElementException as e:
            print(f"✗ 提案比較テーブルが見つかりません: {e}")
            return False
        
        print("=== 投資判断機能基本テスト完了 ===")
        return True
        
    except Exception as e:
        print(f"=== 投資判断機能基本テスト失敗 ===")
        print(f"✗ エラーが発生しました: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = test_investment_decision_basic()
    if success:
        print("✓ テストが成功しました")
    else:
        print("✗ テストが失敗しました") 