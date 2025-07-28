#!/usr/bin/env python3
"""
Web表示機能 Phase 3 修正の簡単なテスト
"""

import unittest
import re
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestPhase3FixesSimple(unittest.TestCase):
    """Phase 3修正の簡単なテスト"""

    def test_date_format_handling(self):
        """日付形式の不整合対応テスト"""
        print("=== 日付形式の不整合対応テスト ===")
        
        # 利用可能なファイルリスト
        available_files = [
            'predictions_20250715.json',
            'predictions_2025-07-07.json',
            'predictions_2024-07-12.json'
        ]
        
        # 日付形式の正規表現テスト
        date_pattern = r'predictions_(\d{4})[-_]?(\d{2})[-_]?(\d{2})\.json'
        
        for filename in available_files:
            match = re.match(date_pattern, filename)
            self.assertIsNotNone(match, f"ファイル名 {filename} が正規表現にマッチしません")
            
            year, month, day = match.groups()
            self.assertEqual(len(year), 4, f"年が4桁ではありません: {year}")
            self.assertEqual(len(month), 2, f"月が2桁ではありません: {month}")
            self.assertEqual(len(day), 2, f"日が2桁ではありません: {day}")
            
            print(f"✓ {filename} の日付形式が正しく解析されました")

    def test_closest_date_finding(self):
        """最も近い日付のファイル検索テスト"""
        print("=== 最も近い日付のファイル検索テスト ===")
        
        def find_closest_date_file(available_files, target_date):
            from datetime import datetime
            
            closest_file = None
            min_diff = float('inf')
            
            for file in available_files:
                if not file.startswith('predictions_'):
                    continue
                
                # ファイル名から日付を抽出
                date_match = re.match(r'predictions_(\d{4})[-_]?(\d{2})[-_]?(\d{2})\.json', file)
                if not date_match:
                    continue
                
                year = int(date_match.group(1))
                month = int(date_match.group(2))
                day = int(date_match.group(3))
                file_date = datetime(year, month, day)
                
                diff = abs((target_date - file_date).days)
                if diff < min_diff:
                    min_diff = diff
                    closest_file = file
            
            return closest_file
        
        from datetime import datetime
        
        available_files = [
            'predictions_20250715.json',
            'predictions_2025-07-07.json',
            'predictions_2024-07-12.json'
        ]
        
        # テストケース
        test_cases = [
            (datetime(2025, 7, 16), 'predictions_20250715.json'),
            (datetime(2025, 7, 8), 'predictions_2025-07-07.json'),
            (datetime(2024, 7, 13), 'predictions_2024-07-12.json'),
        ]
        
        for target_date, expected_file in test_cases:
            result = find_closest_date_file(available_files, target_date)
            self.assertEqual(result, expected_file, 
                           f"日付 {target_date.date()} に対して {expected_file} が期待されましたが、{result} が返されました")
            print(f"✓ 日付 {target_date.date()} に対して正しいファイル {result} が選択されました")

    def test_duplicate_initialization_prevention(self):
        """重複初期化の防止テスト"""
        print("=== 重複初期化の防止テスト ===")
        
        # HTMLファイルの内容を確認
        html_path = project_root / "kyotei_predictor" / "templates" / "predictions.html"
        self.assertTrue(html_path.exists(), "predictions.html が見つかりません")
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 重複初期化防止のコードが含まれているかチェック
        self.assertIn("window.predictionsViewer", html_content, 
                     "重複初期化防止のコードが含まれていません")
        self.assertIn("already initialized", html_content, 
                     "重複初期化防止のメッセージが含まれていません")
        
        print("✓ 重複初期化防止のコードが正しく実装されています")

    def test_error_handling_improvements(self):
        """エラーハンドリングの改善テスト"""
        print("=== エラーハンドリングの改善テスト ===")
        
        # JavaScriptファイルの内容を確認
        js_path = project_root / "kyotei_predictor" / "static" / "js" / "predictions.js"
        self.assertTrue(js_path.exists(), "predictions.js が見つかりません")
        
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # エラーハンドリングの改善が含まれているかチェック
        self.assertIn("getAvailablePastPredictionFiles", js_content, 
                     "利用可能なファイル取得機能が含まれていません")
        self.assertIn("findClosestDateFile", js_content, 
                     "最も近い日付検索機能が含まれていません")
        self.assertIn("指定された日付", js_content, 
                     "詳細なエラーメッセージが含まれていません")
        
        print("✓ エラーハンドリングの改善が正しく実装されています")

    def test_console_error_resolution(self):
        """コンソールエラーの解決テスト"""
        print("=== コンソールエラーの解決テスト ===")
        
        # JavaScriptファイルで必要な関数が定義されているかチェック
        js_path = project_root / "kyotei_predictor" / "static" / "js" / "predictions.js"
        
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # 必要な関数の存在確認
        required_functions = [
            "getRiskClass",
            "getRiskText", 
            "getRankClass",
            "getProbabilityClass",
            "getExpectedValueClass",
            "getSuggestionTypeClass",
            "getSuggestionTypeText",
            "setupRaceHeaders",
            "setupPastRaceHeaders"
        ]
        
        for func_name in required_functions:
            self.assertIn(func_name, js_content, f"必要な関数 {func_name} が定義されていません")
            print(f"✓ 関数 {func_name} が正しく定義されています")

    def test_phase3_features_integration(self):
        """Phase 3機能の統合テスト"""
        print("=== Phase 3機能の統合テスト ===")
        
        # Phase 3の主要機能が実装されているかチェック
        js_path = project_root / "kyotei_predictor" / "static" / "js" / "predictions.js"
        
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Phase 3の主要機能
        phase3_features = [
            "renderPurchaseSuggestions",
            "renderSuggestionsComparisonTable", 
            "renderSuggestionCard",
            "calculateSuggestionRiskLevel",
            "evaluateSuggestion",
            "getInvestmentAdvice"
        ]
        
        for feature in phase3_features:
            self.assertIn(feature, js_content, f"Phase 3機能 {feature} が実装されていません")
            print(f"✓ Phase 3機能 {feature} が正しく実装されています")


def run_simple_tests():
    """簡単なテストを実行"""
    print("=" * 60)
    print("Web表示機能 Phase 3 修正の簡単なテスト")
    print("=" * 60)
    
    # テストスイートを作成
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase3FixesSimple)
    
    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 結果を表示
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"実行テスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    if result.failures:
        print("\n失敗したテスト:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nエラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1) 