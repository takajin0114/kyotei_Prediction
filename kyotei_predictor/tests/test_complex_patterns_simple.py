#!/usr/bin/env python3
"""
複雑な購入パターンの簡単テスト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kyotei_predictor.tools.prediction_tool import PredictionTool


def test_complex_patterns():
    """複雑なパターンの動作テスト"""
    print("=" * 60)
    print("複雑な購入パターンの動作テスト")
    print("=" * 60)
    
    # PredictionToolのインスタンスを作成
    tool = PredictionTool()
    
    # テスト用の組み合わせデータ
    test_combinations = [
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
    
    print("📊 テスト用組み合わせデータ:")
    for combo in test_combinations:
        print(f"  {combo['combination']}: {combo['probability']:.3f}")
    
    print("\n" + "=" * 60)
    print("1. 複雑な流しパターンのテスト")
    print("=" * 60)
    
    # 複雑な流しパターンを生成
    complex_wheel_suggestions = tool.generate_complex_wheel_suggestions(test_combinations)
    
    print(f"生成された複雑な流しパターン数: {len(complex_wheel_suggestions)}件")
    
    for i, suggestion in enumerate(complex_wheel_suggestions, 1):
        print(f"\n📋 パターン{i}: {suggestion['description']}")
        print(f"  🏷️ タイプ: {suggestion['type']}")
        print(f"  💰 購入金額: {suggestion['total_cost']}円")
        print(f"  🎯 購入組数: {suggestion['total_cost'] // 100}組")
        print(f"  📈 上位組み合わせ: {len(suggestion['combinations'])}組")
        print(f"  📊 合計確率: {suggestion['total_probability']:.3f}")
        print(f"  💵 期待リターン: {suggestion['expected_return']:.1f}")
        
        # 組み合わせの詳細
        if len(suggestion['combinations']) <= 10:
            print(f"  🔢 組み合わせ: {', '.join(suggestion['combinations'])}")
        else:
            print(f"  🔢 組み合わせ: {', '.join(suggestion['combinations'][:5])}... (他{len(suggestion['combinations'])-5}組)")
    
    print("\n" + "=" * 60)
    print("2. 高度なフォーメーションパターンのテスト")
    print("=" * 60)
    
    # 高度なフォーメーションパターンを生成
    advanced_formation_suggestions = tool.generate_advanced_formation_suggestions(test_combinations)
    
    print(f"生成された高度なフォーメーションパターン数: {len(advanced_formation_suggestions)}件")
    
    for i, suggestion in enumerate(advanced_formation_suggestions, 1):
        print(f"\n📋 パターン{i}: {suggestion['description']}")
        print(f"  🏷️ タイプ: {suggestion['type']}")
        print(f"  💰 購入金額: {suggestion['total_cost']}円")
        print(f"  🎯 購入組数: {suggestion['total_cost'] // 100}組")
        print(f"  📈 上位組み合わせ: {len(suggestion['combinations'])}組")
        print(f"  📊 合計確率: {suggestion['total_probability']:.3f}")
        print(f"  💵 期待リターン: {suggestion['expected_return']:.1f}")
        
        # 組み合わせの詳細
        if len(suggestion['combinations']) <= 10:
            print(f"  🔢 組み合わせ: {', '.join(suggestion['combinations'])}")
        else:
            print(f"  🔢 組み合わせ: {', '.join(suggestion['combinations'][:5])}... (他{len(suggestion['combinations'])-5}組)")
    
    print("\n" + "=" * 60)
    print("3. 統合テスト（全てのパターン）")
    print("=" * 60)
    
    # 全ての購入提案を生成
    all_suggestions = tool.generate_purchase_suggestions(test_combinations)
    
    print(f"生成された総購入提案数: {len(all_suggestions)}件")
    
    # タイプ別集計
    type_counts = {}
    for suggestion in all_suggestions:
        suggestion_type = suggestion.get('type', 'unknown')
        type_counts[suggestion_type] = type_counts.get(suggestion_type, 0) + 1
    
    print(f"\n📈 タイプ別集計:")
    for type_name, count in type_counts.items():
        print(f"  {type_name}: {count}件")
    
    # 新しいタイプの確認
    new_types = ['complex_wheel', 'advanced_formation']
    print(f"\n🆕 新しいタイプの確認:")
    for new_type in new_types:
        if new_type in type_counts:
            print(f"  ✅ {new_type}: {type_counts[new_type]}件")
        else:
            print(f"  ⚠️ {new_type}: 0件（データに依存）")
    
    print("\n" + "=" * 60)
    print("4. 購入組数の検証")
    print("=" * 60)
    
    # 各提案の購入組数を検証
    for i, suggestion in enumerate(all_suggestions, 1):
        total_cost = suggestion['total_cost']
        combinations_count = len(suggestion['combinations'])
        calculated_combinations = total_cost // 100
        
        print(f"\n📋 提案{i}: {suggestion['description']}")
        print(f"  🏷️ タイプ: {suggestion['type']}")
        print(f"  💰 購入金額: {total_cost}円")
        print(f"  🎯 計算組数: {calculated_combinations}組")
        print(f"  📈 上位組み合わせ: {combinations_count}組")
        
        # 検証
        if calculated_combinations > 0:
            print(f"  ✅ 購入組数: 正常")
        else:
            print(f"  ❌ 購入組数: 異常（0組）")
        
        if combinations_count <= calculated_combinations:
            print(f"  ✅ 組み合わせ数: 正常")
        else:
            print(f"  ❌ 組み合わせ数: 異常（購入組数を超過）")
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_complex_patterns()
    sys.exit(0 if success else 1) 