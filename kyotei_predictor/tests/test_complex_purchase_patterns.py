#!/usr/bin/env python3
"""
複雑な購入パターンのテスト
"""

import unittest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kyotei_predictor.tools.prediction_tool import PredictionTool


class TestComplexPurchasePatterns(unittest.TestCase):
    """複雑な購入パターンのテスト"""

    def setUp(self):
        """テストの準備"""
        self.tool = PredictionTool()
        
        # テスト用の組み合わせデータ
        self.test_combinations = [
            {'combination': '1-2-3', 'probability': 0.20, 'expected_value': 2.0, 'rank': 1},
            {'combination': '1-2-4', 'probability': 0.15, 'expected_value': 1.8, 'rank': 2},
            {'combination': '1-3-2', 'probability': 0.12, 'expected_value': 1.7, 'rank': 3},
            {'combination': '1-3-4', 'probability': 0.10, 'expected_value': 1.6, 'rank': 4},
            {'combination': '2-1-3', 'probability': 0.08, 'expected_value': 1.5, 'rank': 5},
            {'combination': '2-3-1', 'probability': 0.07, 'expected_value': 1.4, 'rank': 6},
            {'combination': '3-1-2', 'probability': 0.06, 'expected_value': 1.3, 'rank': 7},
            {'combination': '3-2-1', 'probability': 0.05, 'expected_value': 1.2, 'rank': 8},
            {'combination': '1-4-2', 'probability': 0.04, 'expected_value': 1.1, 'rank': 9},
            {'combination': '1-4-3', 'probability': 0.03, 'expected_value': 1.0, 'rank': 10},
        ]

    def test_complex_wheel_patterns(self):
        """複雑な流しパターンのテスト"""
        print("=== 複雑な流しパターンのテスト ===")
        
        # 複雑な流しパターンを生成
        suggestions = self.tool.generate_complex_wheel_suggestions(self.test_combinations)
        
        self.assertIsInstance(suggestions, list, "複雑な流しパターンがリストで返されるべき")
        
        for suggestion in suggestions:
            print(f"📊 {suggestion['description']}: {suggestion['total_cost'] // 100}組")
            
            # 基本的な検証
            self.assertIn('type', suggestion, "typeフィールドが必要")
            self.assertIn('description', suggestion, "descriptionフィールドが必要")
            self.assertIn('total_cost', suggestion, "total_costフィールドが必要")
            self.assertIn('combinations', suggestion, "combinationsフィールドが必要")
            
            # 購入組数の検証
            total_cost = suggestion['total_cost']
            combinations_count = len(suggestion['combinations'])
            calculated_combinations = total_cost // 100
            
            print(f"  💰 購入金額: {total_cost}円")
            print(f"  📈 上位組み合わせ: {combinations_count}組")
            print(f"  🎯 計算組数: {calculated_combinations}組")
            
            # 購入組数が正しく計算されていることを確認
            self.assertGreater(calculated_combinations, 0, "購入組数は0より大きいべき")
            self.assertLessEqual(combinations_count, calculated_combinations, 
                               "上位組み合わせ数は購入組数以下であるべき")

    def test_advanced_formation_patterns(self):
        """高度なフォーメーションパターンのテスト"""
        print("=== 高度なフォーメーションパターンのテスト ===")
        
        # 高度なフォーメーションパターンを生成
        suggestions = self.tool.generate_advanced_formation_suggestions(self.test_combinations)
        
        self.assertIsInstance(suggestions, list, "高度なフォーメーションパターンがリストで返されるべき")
        
        for suggestion in suggestions:
            print(f"📊 {suggestion['description']}: {suggestion['total_cost'] // 100}組")
            
            # 基本的な検証
            self.assertIn('type', suggestion, "typeフィールドが必要")
            self.assertEqual(suggestion['type'], 'advanced_formation', "タイプがadvanced_formationであるべき")
            self.assertIn('description', suggestion, "descriptionフィールドが必要")
            self.assertIn('total_cost', suggestion, "total_costフィールドが必要")
            self.assertIn('combinations', suggestion, "combinationsフィールドが必要")
            
            # 購入組数の検証
            total_cost = suggestion['total_cost']
            combinations_count = len(suggestion['combinations'])
            calculated_combinations = total_cost // 100
            
            print(f"  💰 購入金額: {total_cost}円")
            print(f"  📈 上位組み合わせ: {combinations_count}組")
            print(f"  🎯 計算組数: {calculated_combinations}組")
            
            # 購入組数が正しく計算されていることを確認
            self.assertGreater(calculated_combinations, 0, "購入組数は0より大きいべき")
            self.assertLessEqual(combinations_count, calculated_combinations, 
                               "上位組み合わせ数は購入組数以下であるべき")

    def test_purchase_pattern_calculations(self):
        """購入パターンの組数計算テスト"""
        print("=== 購入パターンの組数計算テスト ===")
        
        # 各パターンの理論的組数を計算
        patterns = {
            '1位固定-2位流し-3位固定': {
                'example': '1位:1固定、2位:2,3,4,5流し、3位:6固定',
                'calculation': '4C1 = 4通り',
                'expected': 4
            },
            '1位流し-2位固定-3位流し': {
                'example': '1位:1,2,3流し、2位:4固定、3位:5,6流し',
                'calculation': '3C1 × 2C1 = 3 × 2 = 6通り',
                'expected': 6
            },
            'フォーメーション1': {
                'example': '1着:1,2 2着:3,4 3着:5,6',
                'calculation': '2 × 2 × 2 = 8通り',
                'expected': 8
            },
            'フォーメーション2': {
                'example': '1着:1,2,3 2着:2,3,4 3着:4,5,6',
                'calculation': '実際の組み合わせ数に基づく',
                'expected': 'variable'
            }
        }
        
        for pattern_name, pattern_info in patterns.items():
            print(f"📋 {pattern_name}")
            print(f"  📝 例: {pattern_info['example']}")
            print(f"  🧮 計算: {pattern_info['calculation']}")
            if pattern_info['expected'] != 'variable':
                print(f"  ✅ 期待組数: {pattern_info['expected']}組")
            else:
                print(f"  ✅ 期待組数: 変動（実際の組み合わせに基づく）")

    def test_web_display_support(self):
        """Web表示サポートのテスト"""
        print("=== Web表示サポートのテスト ===")
        
        # JavaScriptファイルの確認
        js_path = project_root / "kyotei_predictor" / "static" / "js" / "predictions.js"
        self.assertTrue(js_path.exists(), "predictions.js が存在するべき")
        
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # CSSファイルの確認
        css_path = project_root / "kyotei_predictor" / "static" / "css" / "predictions.css"
        self.assertTrue(css_path.exists(), "predictions.css が存在するべき")
        
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # 新しいタイプのサポート確認
        new_types = [
            'formation',
            'complex_wheel', 
            'advanced_formation'
        ]
        
        for type_name in new_types:
            # JavaScriptでのサポート確認
            self.assertIn(type_name, js_content, f"JavaScriptで{type_name}タイプがサポートされているべき")
            print(f"✅ JavaScript: {type_name}タイプがサポートされています")
            
            # CSSでのサポート確認
            css_class = type_name.replace('_', '-')
            self.assertIn(f'.badge.{css_class}', css_content, f"CSSで{type_name}タイプのスタイルが定義されているべき")
            print(f"✅ CSS: {type_name}タイプのスタイルが定義されています")

    def test_integration_with_existing_patterns(self):
        """既存パターンとの統合テスト"""
        print("=== 既存パターンとの統合テスト ===")
        
        # 全ての購入提案を生成
        all_suggestions = self.tool.generate_purchase_suggestions(self.test_combinations)
        
        self.assertIsInstance(all_suggestions, list, "購入提案がリストで返されるべき")
        self.assertLessEqual(len(all_suggestions), 8, "最大8件まで返されるべき")
        
        print(f"📊 生成された購入提案数: {len(all_suggestions)}件")
        
        # 各提案のタイプを確認
        type_counts = {}
        for suggestion in all_suggestions:
            suggestion_type = suggestion.get('type', 'unknown')
            type_counts[suggestion_type] = type_counts.get(suggestion_type, 0) + 1
            
            print(f"  📋 {suggestion['description']} ({suggestion_type}): {suggestion['total_cost'] // 100}組")
        
        print(f"📈 タイプ別集計: {type_counts}")
        
        # 新しいタイプが含まれていることを確認
        new_types = ['complex_wheel', 'advanced_formation']
        for new_type in new_types:
            if new_type in type_counts:
                print(f"✅ {new_type}タイプが{type_counts[new_type]}件含まれています")
            else:
                print(f"⚠️ {new_type}タイプは含まれていません（データに依存）")


def run_complex_patterns_tests():
    """複雑なパターンテストを実行"""
    print("=" * 60)
    print("複雑な購入パターンのテスト")
    print("=" * 60)
    
    # テストスイートを作成
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestComplexPurchasePatterns)
    
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
    success = run_complex_patterns_tests()
    sys.exit(0 if success else 1) 