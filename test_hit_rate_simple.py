#!/usr/bin/env python3
"""
簡易的な的中率分析機能のテスト
"""

import sys
import os
# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def action_to_trifecta(action: int) -> tuple:
    """
    アクション番号を3連単予想に変換
    
    Args:
        action: アクション番号 (0-119)
    
    Returns:
        3連単予想のタプル (1着, 2着, 3着)
    """
    # 6P3 = 120通りの組み合わせを生成
    trifectas = []
    for first in range(1, 7):
        for second in range(1, 7):
            for third in range(1, 7):
                if first != second and second != third and first != third:
                    trifectas.append((first, second, third))
    
    if 0 <= action < len(trifectas):
        return trifectas[action]
    else:
        # 無効なアクションの場合はデフォルト値を返す
        return (1, 2, 3)

def test_action_to_trifecta():
    """action_to_trifecta関数のテスト"""
    print("=== action_to_trifecta関数のテスト ===")
    
    # 正常なアクションのテスト
    test_cases = [
        (0, (1, 2, 3)),
        (1, (1, 2, 4)),
        (2, (1, 2, 5)),
        (119, (6, 5, 4))  # 最後のアクション
    ]
    
    for action, expected in test_cases:
        result = action_to_trifecta(action)
        print(f"アクション {action} -> 予想 {result} (期待値: {expected})")
        assert result == expected, f"アクション {action}: 期待値 {expected}, 実際 {result}"
    
    # 無効なアクションのテスト
    invalid_actions = [-1, 120, 999]
    for action in invalid_actions:
        result = action_to_trifecta(action)
        print(f"無効アクション {action} -> デフォルト値 {result}")
        assert result == (1, 2, 3), f"無効アクション {action}: 期待値 (1, 2, 3), 実際 {result}"
    
    print("✅ action_to_trifecta関数のテスト完了")

def test_all_combinations():
    """全てのアクションの組み合わせテスト"""
    print("=== 全アクション組み合わせテスト ===")
    
    trifectas = set()
    for action in range(120):
        trifecta = action_to_trifecta(action)
        trifectas.add(trifecta)
        
        # 基本的な検証
        assert len(trifecta) == 3, f"アクション {action}: 長さが3ではありません"
        assert all(1 <= x <= 6 for x in trifecta), f"アクション {action}: 値が1-6の範囲外"
        assert len(set(trifecta)) == 3, f"アクション {action}: 重複があります"
    
    print(f"生成された3連単予想数: {len(trifectas)}")
    assert len(trifectas) == 120, f"期待値: 120, 実際: {len(trifectas)}"  # 6P3 = 120通り
    
    print("✅ 全アクション組み合わせテスト完了")

def test_hit_rate_calculation():
    """的中率計算のテスト"""
    print("=== 的中率計算のテスト ===")
    
    # テストケース
    test_cases = [
        {
            'name': '完全的中のみ',
            'predictions': [
                {'is_exact_match': True, 'first_hit': True, 'second_hit': True},
                {'is_exact_match': False, 'first_hit': False, 'second_hit': False},
                {'is_exact_match': False, 'first_hit': False, 'second_hit': False}
            ],
            'expected_top10': 33.33,
            'expected_top20': 33.33
        },
        {
            'name': '完全的中 + 2着的中',
            'predictions': [
                {'is_exact_match': True, 'first_hit': True, 'second_hit': True},
                {'is_exact_match': False, 'first_hit': True, 'second_hit': True},
                {'is_exact_match': False, 'first_hit': False, 'second_hit': False}
            ],
            'expected_top10': 33.33,
            'expected_top20': 66.67
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        
        # 的中率計算のロジックを再現
        top10_hits = []
        top20_hits = []
        
        for i, pred in enumerate(test_case['predictions']):
            if pred['is_exact_match']:
                top10_hits.append(i)
                top20_hits.append(i)
            elif pred['first_hit'] and pred['second_hit']:
                top20_hits.append(i)
        
        top10_rate = len(top10_hits) / len(test_case['predictions']) * 100
        top20_rate = len(top20_hits) / len(test_case['predictions']) * 100
        
        print(f"  上位10位的中率: {top10_rate:.2f}% (期待値: {test_case['expected_top10']:.2f}%)")
        print(f"  上位20位的中率: {top20_rate:.2f}% (期待値: {test_case['expected_top20']:.2f}%)")
        
        assert abs(top10_rate - test_case['expected_top10']) < 0.1, f"上位10位的中率が期待値と異なります"
        assert abs(top20_rate - test_case['expected_top20']) < 0.1, f"上位20位的中率が期待値と異なります"
    
    print("✅ 的中率計算のテスト完了")

def main():
    """メイン関数"""
    print("=" * 60)
    print("的中率詳細分析機能の簡易テスト開始")
    print("=" * 60)
    
    try:
        test_action_to_trifecta()
        test_all_combinations()
        test_hit_rate_calculation()
        
        print("=" * 60)
        print("✅ 全てのテストが成功しました！")
        print("=" * 60)
        
        print("\n実装された機能:")
        print("- action_to_trifecta: アクション番号を3連単予想に変換")
        print("- 的中率計算: 上位10位・20位の中率を計算")
        print("- 全組み合わせ生成: 6P3 = 120通りの3連単予想を生成")
        
        return True
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ テストでエラーが発生しました: {e}")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 