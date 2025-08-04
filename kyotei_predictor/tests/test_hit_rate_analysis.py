#!/usr/bin/env python3
"""
的中率詳細分析機能のテストスクリプト
"""

import sys
import os
import unittest
import tempfile
import json
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from kyotei_predictor.tools.evaluation.analyze_hit_rate_detailed import (
    action_to_trifecta,
    analyze_hit_rate_detailed,
    create_detailed_hit_rate_plots
)

class TestHitRateAnalysis(unittest.TestCase):
    """的中率詳細分析機能のテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.test_model_path = "./test_model.zip"
        self.test_data_dir = "kyotei_predictor/data/raw/2024-02"
        self.test_n_episodes = 10
        self.test_top_n_list = [10, 20]
    
    def test_action_to_trifecta(self):
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
            with self.subTest(action=action):
                result = action_to_trifecta(action)
                print(f"アクション {action} -> 予想 {result} (期待値: {expected})")
                self.assertEqual(result, expected)
        
        # 無効なアクションのテスト
        invalid_actions = [-1, 120, 999]
        for action in invalid_actions:
            with self.subTest(action=action):
                result = action_to_trifecta(action)
                print(f"無効アクション {action} -> デフォルト値 {result}")
                self.assertEqual(result, (1, 2, 3))
        
        print("✅ action_to_trifecta関数のテスト完了")
    
    def test_action_to_trifecta_all_combinations(self):
        """全てのアクションの組み合わせテスト"""
        print("=== 全アクション組み合わせテスト ===")
        
        trifectas = set()
        for action in range(120):
            trifecta = action_to_trifecta(action)
            trifectas.add(trifecta)
            
            # 基本的な検証
            self.assertEqual(len(trifecta), 3)
            self.assertTrue(all(1 <= x <= 6 for x in trifecta))
            self.assertEqual(len(set(trifecta)), 3)  # 重複なし
        
        print(f"生成された3連単予想数: {len(trifectas)}")
        self.assertEqual(len(trifectas), 120)  # 6P3 = 120通り
        
        print("✅ 全アクション組み合わせテスト完了")
    
    @patch('kyotei_predictor.tools.evaluation.analyze_hit_rate_detailed.PPO')
    @patch('kyotei_predictor.tools.evaluation.analyze_hit_rate_detailed.KyoteiEnvManager')
    @patch('kyotei_predictor.tools.evaluation.analyze_hit_rate_detailed.DummyVecEnv')
    def test_analyze_hit_rate_detailed_mock(self, mock_dummy_vec_env, mock_env_manager, mock_ppo):
        """モックを使用したanalyze_hit_rate_detailed関数のテスト"""
        print("=== analyze_hit_rate_detailed関数のモックテスト ===")
        
        # モックの設定
        mock_model = Mock()
        mock_ppo.load.return_value = mock_model
        
        mock_env = Mock()
        mock_dummy_vec_env.return_value = mock_env
        
        # テスト用の予測データを生成
        test_predictions = []
        for episode in range(5):
            # 完全的中、2着的中、不的中を混在させる
            if episode == 0:
                # 完全的中
                prediction_data = {
                    'episode': episode,
                    'predicted_trifecta': (1, 2, 3),
                    'actual_arrival': (1, 2, 3),
                    'is_exact_match': True,
                    'first_hit': True,
                    'second_hit': True,
                    'reward': 1000.0
                }
            elif episode == 1:
                # 2着的中
                prediction_data = {
                    'episode': episode,
                    'predicted_trifecta': (1, 2, 4),
                    'actual_arrival': (1, 2, 3),
                    'is_exact_match': False,
                    'first_hit': True,
                    'second_hit': True,
                    'reward': 500.0
                }
            else:
                # 不的中
                prediction_data = {
                    'episode': episode,
                    'predicted_trifecta': (2, 3, 4),
                    'actual_arrival': (1, 2, 3),
                    'is_exact_match': False,
                    'first_hit': False,
                    'second_hit': False,
                    'reward': -100.0
                }
            test_predictions.append(prediction_data)
        
        # 環境のステップ動作をモック
        def mock_step(action):
            episode = len(test_predictions) - 1
            if episode < len(test_predictions):
                pred = test_predictions[episode]
                return (
                    np.random.random((1, 6, 8)),  # obs
                    np.array([pred['reward']]),    # reward
                    True,                          # done
                    [{'arrival': pred['actual_arrival']}]  # info
                )
            return (np.random.random((1, 6, 8)), np.array([0]), True, [{}])
        
        mock_env.step.side_effect = mock_step
        mock_env.reset.return_value = np.random.random((1, 6, 8))
        
        # モデルの予測をモック
        def mock_predict(obs, deterministic=True):
            episode = len(test_predictions) - 1
            if episode < len(test_predictions):
                pred = test_predictions[episode]
                # 予想をアクション番号に変換（簡略化）
                action_num = episode % 120
                return np.array([action_num]), None
            return np.array([0]), None
        
        mock_model.predict.side_effect = mock_predict
        
        # 可視化関数をモック
        with patch('kyotei_predictor.tools.evaluation.analyze_hit_rate_detailed.create_detailed_hit_rate_plots') as mock_plot:
            # テスト実行
            result = analyze_hit_rate_detailed(
                model_path=self.test_model_path,
                n_eval_episodes=5,
                data_dir=self.test_data_dir,
                top_n_list=[10, 20]
            )
        
        # 結果の検証
        self.assertIsNotNone(result)
        self.assertIn('hit_rate_analysis', result)
        self.assertIn('exact_matches', result)
        self.assertIn('first_second_hits', result)
        self.assertIn('all_predictions', result)
        
        # 的中率の検証
        hit_analysis = result['hit_rate_analysis']
        self.assertIn('top_10', hit_analysis)
        self.assertIn('top_20', hit_analysis)
        
        print(f"完全的中数: {result['exact_matches']}")
        print(f"2着的中数: {result['first_second_hits']}")
        print(f"上位10位的中率: {hit_analysis['top_10']['hit_rate']:.2f}%")
        print(f"上位20位的中率: {hit_analysis['top_20']['hit_rate']:.2f}%")
        
        print("✅ analyze_hit_rate_detailed関数のモックテスト完了")
    
    def test_create_detailed_hit_rate_plots(self):
        """可視化関数のテスト"""
        print("=== create_detailed_hit_rate_plots関数のテスト ===")
        
        # テスト用データの作成
        all_predictions = []
        for episode in range(10):
            if episode < 3:
                # 完全的中
                prediction_data = {
                    'episode': episode,
                    'predicted_trifecta': (1, 2, 3),
                    'actual_arrival': (1, 2, 3),
                    'is_exact_match': True,
                    'first_hit': True,
                    'second_hit': True,
                    'reward': 1000.0
                }
            elif episode < 6:
                # 2着的中
                prediction_data = {
                    'episode': episode,
                    'predicted_trifecta': (1, 2, 4),
                    'actual_arrival': (1, 2, 3),
                    'is_exact_match': False,
                    'first_hit': True,
                    'second_hit': True,
                    'reward': 500.0
                }
            else:
                # 不的中
                prediction_data = {
                    'episode': episode,
                    'predicted_trifecta': (2, 3, 4),
                    'actual_arrival': (1, 2, 3),
                    'is_exact_match': False,
                    'first_hit': False,
                    'second_hit': False,
                    'reward': -100.0
                }
            all_predictions.append(prediction_data)
        
        hit_rate_analysis = {
            'top_10': {'hit_rate': 30.0, 'hit_count': 3},
            'top_20': {'hit_rate': 60.0, 'hit_count': 6}
        }
        top_n_list = [10, 20]
        
        # 可視化関数のテスト（エラーが発生しないことを確認）
        try:
            with patch('matplotlib.pyplot.show'):
                create_detailed_hit_rate_plots(all_predictions, hit_rate_analysis, top_n_list)
            print("✅ 可視化関数のテスト完了")
        except Exception as e:
            self.fail(f"可視化関数でエラーが発生: {e}")
    
    def test_hit_rate_calculation(self):
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
            with self.subTest(name=test_case['name']):
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
                
                print(f"{test_case['name']}:")
                print(f"  上位10位的中率: {top10_rate:.2f}% (期待値: {test_case['expected_top10']:.2f}%)")
                print(f"  上位20位的中率: {top20_rate:.2f}% (期待値: {test_case['expected_top20']:.2f}%)")
                
                self.assertAlmostEqual(top10_rate, test_case['expected_top10'], places=1)
                self.assertAlmostEqual(top20_rate, test_case['expected_top20'], places=1)
        
        print("✅ 的中率計算のテスト完了")

def run_hit_rate_analysis_tests():
    """的中率詳細分析機能のテスト実行"""
    print("=" * 60)
    print("的中率詳細分析機能のテスト開始")
    print("=" * 60)
    
    # テストスイートの作成
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestHitRateAnalysis)
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("=" * 60)
    print("的中率詳細分析機能のテスト結果")
    print("=" * 60)
    print(f"実行テスト数: {result.testsRun}")
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
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nテスト結果: {'✅ 成功' if success else '❌ 失敗'}")
    
    return success

if __name__ == "__main__":
    success = run_hit_rate_analysis_tests()
    sys.exit(0 if success else 1) 