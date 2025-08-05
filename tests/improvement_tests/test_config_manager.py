#!/usr/bin/env python3
"""
設定管理クラスのテストスクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加（相対パス）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'kyotei_predictor'))

def test_config_manager():
    """設定管理クラスのテスト"""
    print("=== 設定管理クラステスト開始 ===")
    
    try:
        from config.improvement_config_manager import ImprovementConfigManager
        
        # 設定管理クラスのインスタンスを作成
        config_manager = ImprovementConfigManager()
        print("設定管理クラスの作成成功 ✓")
        
        # 設定サマリーを表示
        print("\n--- 設定サマリー ---")
        config_manager.print_config_summary()
        
        # 特定のパラメータを取得してテスト
        print("\n--- パラメータ取得テスト ---")
        
        # 報酬設計パラメータ
        reward_params = config_manager.get_reward_params("phase1")
        print(f"Phase 1 報酬設計パラメータ: {reward_params}")
        
        # 学習パラメータ
        learning_params = config_manager.get_learning_params("phase2", "normal")
        print(f"Phase 2 学習パラメータ（通常）: {learning_params}")
        
        learning_params_test = config_manager.get_learning_params("phase2", "test_mode")
        print(f"Phase 2 学習パラメータ（テスト）: {learning_params_test}")
        
        learning_params_minimal = config_manager.get_learning_params("phase2", "minimal_mode")
        print(f"Phase 2 学習パラメータ（最小限）: {learning_params_minimal}")
        
        # ハイパーパラメータ
        hyperparams = config_manager.get_hyperparameters("phase2")
        print(f"Phase 2 ハイパーパラメータ: {hyperparams}")
        
        # アンサンブルパラメータ
        ensemble_params = config_manager.get_ensemble_params()
        print(f"Phase 3 アンサンブルパラメータ: {ensemble_params}")
        
        # 継続的学習パラメータ
        continuous_params = config_manager.get_continuous_learning_params()
        print(f"Phase 4 継続的学習パラメータ: {continuous_params}")
        
        # 監視パラメータ
        monitoring_params = config_manager.get_monitoring_params()
        print(f"監視パラメータ: {monitoring_params}")
        
        # テストパラメータ
        testing_params = config_manager.get_testing_params()
        print(f"テストパラメータ: {testing_params}")
        
        # パス設定
        paths = config_manager.get_paths()
        print(f"パス設定: {paths}")
        
        # 設定の妥当性を検証
        print("\n--- 設定妥当性検証 ---")
        is_valid = config_manager.validate_config()
        print(f"設定妥当性: {'✓' if is_valid else '✗'}")
        
        # 設定の更新テスト
        print("\n--- 設定更新テスト ---")
        test_updates = {
            "reward_design": {
                "phase1": {
                    "win_multiplier": 1.6,
                    "partial_second_hit_reward": 15
                }
            }
        }
        
        print("設定を更新中...")
        config_manager.update_config(test_updates)
        
        # 更新後のパラメータを確認
        updated_reward_params = config_manager.get_reward_params("phase1")
        print(f"更新後の報酬パラメータ: {updated_reward_params}")
        
        print("\n=== 設定管理クラステスト完了 ✓ ===")
        return True
        
    except Exception as e:
        print(f"設定管理クラステストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_file_loading():
    """設定ファイル読み込みテスト"""
    print("\n=== 設定ファイル読み込みテスト ===")
    
    try:
        from config.improvement_config_manager import ImprovementConfigManager
        
        # デフォルトパスで設定管理クラスを作成
        config_manager = ImprovementConfigManager()
        
        # 設定ファイルの内容を確認
        config = config_manager.config
        
        # 必須セクションの存在確認
        required_sections = [
            "reward_design", "learning_parameters", "hyperparameters",
            "ensemble", "continuous_learning", "monitoring", "testing", "paths"
        ]
        
        for section in required_sections:
            if section in config:
                print(f"✓ {section} セクションが存在します")
            else:
                print(f"✗ {section} セクションが存在しません")
                return False
        
        # 報酬設計パラメータの詳細確認
        reward_design = config.get("reward_design", {})
        if "phase1" in reward_design and "original" in reward_design:
            print("✓ 報酬設計パラメータが正しく設定されています")
        else:
            print("✗ 報酬設計パラメータが不完全です")
            return False
        
        print("=== 設定ファイル読み込みテスト完了 ✓ ===")
        return True
        
    except Exception as e:
        print(f"設定ファイル読み込みテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parameter_validation():
    """パラメータ検証テスト"""
    print("\n=== パラメータ検証テスト ===")
    
    try:
        from config.improvement_config_manager import ImprovementConfigManager
        
        config_manager = ImprovementConfigManager()
        
        # 報酬パラメータの検証
        reward_params = config_manager.get_reward_params("phase1")
        required_reward_keys = ["win_multiplier", "partial_second_hit_reward", 
                              "partial_first_hit_penalty", "no_hit_penalty"]
        
        for key in required_reward_keys:
            if key in reward_params:
                print(f"✓ 報酬パラメータ '{key}' が存在します: {reward_params[key]}")
            else:
                print(f"✗ 報酬パラメータ '{key}' が存在しません")
                return False
        
        # 学習パラメータの検証
        learning_params = config_manager.get_learning_params("phase2")
        required_learning_keys = ["total_timesteps", "n_eval_episodes"]
        
        for key in required_learning_keys:
            if key in learning_params:
                print(f"✓ 学習パラメータ '{key}' が存在します: {learning_params[key]}")
            else:
                print(f"✗ 学習パラメータ '{key}' が存在しません")
                return False
        
        # ハイパーパラメータの検証
        hyperparams = config_manager.get_hyperparameters("phase2")
        required_hyperparam_keys = ["learning_rate", "batch_size", "n_steps", "gamma"]
        
        for key in required_hyperparam_keys:
            if key in hyperparams:
                print(f"✓ ハイパーパラメータ '{key}' が存在します")
            else:
                print(f"✗ ハイパーパラメータ '{key}' が存在しません")
                return False
        
        print("=== パラメータ検証テスト完了 ✓ ===")
        return True
        
    except Exception as e:
        print(f"パラメータ検証テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン実行関数"""
    print("=== 設定管理クラス 包括的テスト ===")
    
    # 各テストを実行
    test1_success = test_config_manager()
    test2_success = test_config_file_loading()
    test3_success = test_parameter_validation()
    
    print("\n=== テスト結果 ===")
    print(f"設定管理クラステスト: {'成功 ✓' if test1_success else '失敗 ✗'}")
    print(f"設定ファイル読み込みテスト: {'成功 ✓' if test2_success else '失敗 ✗'}")
    print(f"パラメータ検証テスト: {'成功 ✓' if test3_success else '失敗 ✗'}")
    
    if test1_success and test2_success and test3_success:
        print("\nすべてのテストが成功しました！")
        print("設定管理クラスが正常に動作しています。")
        print("次のステップ: 実際の学習処理での設定ファイル活用")
    else:
        print("\n一部のテストが失敗しました。")
        print("エラーの詳細を確認してください。")

if __name__ == "__main__":
    main() 