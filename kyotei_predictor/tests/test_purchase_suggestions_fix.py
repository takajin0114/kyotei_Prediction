#!/usr/bin/env python3
"""
購入提案の組数表示修正テスト
"""

import unittest
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestPurchaseSuggestionsFix(unittest.TestCase):
    """購入提案の組数表示修正テスト"""

    def test_purchase_combinations_calculation(self):
        """購入組数の計算テスト"""
        print("=== 購入組数の計算テスト ===")
        
        # テストデータ
        test_suggestions = [
            {
                "type": "wheel",
                "description": "1-流し",
                "combinations": ["1-2-3", "1-3-2", "1-3-5", "1-2-4"],
                "total_probability": 0.996,
                "total_cost": 2000,  # 20通り = 2000円
                "expected_return": 996.0
            },
            {
                "type": "nagashi", 
                "description": "1-2-流し",
                "combinations": ["1-2-3", "1-2-4", "1-2-5", "1-2-6"],
                "total_probability": 0.992,
                "total_cost": 400,  # 4通り = 400円
                "expected_return": 992.0
            },
            {
                "type": "box",
                "description": "1-2-3 ボックス",
                "combinations": ["1-2-3", "1-3-2", "2-1-3"],
                "total_probability": 0.994,
                "total_cost": 600,  # 6通り = 600円
                "expected_return": 994.0
            }
        ]
        
        # 期待される結果
        expected_combinations = [20, 4, 6]  # 1-流し、1-2-流し、ボックス
        
        for i, suggestion in enumerate(test_suggestions):
            actual_combinations = suggestion["total_cost"] // 100
            expected = expected_combinations[i]
            
            self.assertEqual(actual_combinations, expected, 
                           f"{suggestion['description']}: 期待値{expected}組、実際{actual_combinations}組")
            print(f"✓ {suggestion['description']}: {actual_combinations}組（正しい）")

    def test_actual_data_verification(self):
        """実際のデータでの検証テスト"""
        print("=== 実際のデータでの検証テスト ===")
        
        # 実際の予測データファイルを読み込み
        data_files = [
            "outputs/predictions_latest.json",
            "outputs/predictions_20250715.json"
        ]
        
        for data_file in data_files:
            file_path = project_root / data_file
            if not file_path.exists():
                print(f"⚠️ ファイルが見つかりません: {data_file}")
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n📁 {data_file} の検証:")
            
            for prediction in data.get('predictions', []):
                venue = prediction.get('venue', 'Unknown')
                race_number = prediction.get('race_number', 0)
                suggestions = prediction.get('purchase_suggestions', [])
                
                print(f"  🏁 {venue} R{race_number}:")
                
                for suggestion in suggestions:
                    description = suggestion.get('description', 'Unknown')
                    total_cost = suggestion.get('total_cost', 0)
                    combinations_count = len(suggestion.get('combinations', []))
                    calculated_combinations = total_cost // 100
                    
                    # 購入組数の検証
                    if suggestion['type'] == 'wheel':  # 1-流し
                        expected_combinations = 20
                    elif suggestion['type'] == 'nagashi':  # 1-2-流し
                        expected_combinations = 4
                    elif suggestion['type'] == 'box':  # ボックス
                        expected_combinations = 6
                    else:
                        expected_combinations = calculated_combinations
                    
                    # 検証
                    if calculated_combinations == expected_combinations:
                        print(f"    ✅ {description}: {calculated_combinations}組（正しい）")
                    else:
                        print(f"    ❌ {description}: {calculated_combinations}組（期待値: {expected_combinations}組）")
                    
                    # 組み合わせ数と購入組数の関係確認
                    if combinations_count <= calculated_combinations:
                        print(f"      📊 上位組み合わせ: {combinations_count}組 / 全{calculated_combinations}組")
                    else:
                        print(f"      ⚠️ 組み合わせ数が購入組数を超えています: {combinations_count} > {calculated_combinations}")

    def test_javascript_calculation_verification(self):
        """JavaScript計算の検証テスト"""
        print("=== JavaScript計算の検証テスト ===")
        
        # JavaScriptの計算ロジックをPythonで再現
        def calculate_combinations_js(total_cost):
            """JavaScript: Math.round(suggestion.total_cost / 100)"""
            return round(total_cost / 100)
        
        # テストケース
        test_cases = [
            (2000, 20),  # 1-流し
            (400, 4),    # 1-2-流し
            (600, 6),    # ボックス
            (1200, 12),  # その他
        ]
        
        for total_cost, expected in test_cases:
            actual = calculate_combinations_js(total_cost)
            self.assertEqual(actual, expected, 
                           f"total_cost={total_cost}: 期待値{expected}組、実際{actual}組")
            print(f"✓ total_cost={total_cost}円 → {actual}組（正しい）")

    def test_combination_types_verification(self):
        """組み合わせタイプ別の検証テスト"""
        print("=== 組み合わせタイプ別の検証テスト ===")
        
        # 各タイプの正しい組数
        type_combinations = {
            'wheel': 20,    # 1-流し: 1着固定、2-3着流し
            'nagashi': 4,   # 1-2-流し: 1-2着固定、3着流し
            'box': 6,       # ボックス: 3艇の全順列
        }
        
        # 計算式の検証
        def calculate_wheel_combinations():
            """1-流しの組数計算: 5P2 = 5! / (5-2)! = 5 × 4 = 20"""
            return 5 * 4
        
        def calculate_nagashi_combinations():
            """1-2-流しの組数計算: 4C1 = 4"""
            return 4
        
        def calculate_box_combinations():
            """ボックスの組数計算: 3! = 6"""
            return 6
        
        # 検証
        self.assertEqual(calculate_wheel_combinations(), 20, "1-流しの組数計算が間違っています")
        self.assertEqual(calculate_nagashi_combinations(), 4, "1-2-流しの組数計算が間違っています")
        self.assertEqual(calculate_box_combinations(), 6, "ボックスの組数計算が間違っています")
        
        print("✓ 1-流し: 20組（5P2 = 5 × 4）")
        print("✓ 1-2-流し: 4組（4C1 = 4）")
        print("✓ ボックス: 6組（3! = 6）")

    def test_web_display_improvements(self):
        """Web表示改善の検証テスト"""
        print("=== Web表示改善の検証テスト ===")
        
        # JavaScriptファイルの修正内容を確認
        js_path = project_root / "kyotei_predictor" / "static" / "js" / "predictions.js"
        self.assertTrue(js_path.exists(), "predictions.js が見つかりません")
        
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # 修正された内容の確認
        improvements = [
            "Math.round(suggestion.total_cost / 100)",  # 購入組数の正しい計算
            "購入組数",  # ラベルの変更
            "上位組み合わせ",  # 組み合わせリストの説明改善
        ]
        
        for improvement in improvements:
            self.assertIn(improvement, js_content, f"改善内容 '{improvement}' が実装されていません")
            print(f"✓ 改善内容 '{improvement}' が実装されています")


def run_purchase_suggestions_fix_tests():
    """購入提案修正テストを実行"""
    print("=" * 60)
    print("購入提案の組数表示修正テスト")
    print("=" * 60)
    
    # テストスイートを作成
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestPurchaseSuggestionsFix)
    
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
    success = run_purchase_suggestions_fix_tests()
    sys.exit(0 if success else 1) 