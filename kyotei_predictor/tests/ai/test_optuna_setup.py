#!/usr/bin/env python3
"""
Optuna設定の動作テストスクリプト
ハイパーパラメータ最適化の基本機能をテスト
"""

import sys
import os
import json
import optuna
import numpy as np
from datetime import datetime

# プロジェクトパスの追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kyotei_predictor.tools.ai.optuna_optimizer import KyoteiOptunaOptimizer

def test_config_loading():
    """設定ファイルの読み込みテスト"""
    print("="*50)
    print("1. 設定ファイル読み込みテスト")
    print("="*50)
    
    try:
        config_path = "config/optuna_config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ 設定ファイル読み込み成功")
        print(f"試行回数: {config['optimization']['n_trials']}")
        print(f"最適化対象: {config['optimization']['metric']}")
        print(f"ハイパーパラメータ数: {len(config['hyperparameters'])}")
        
        return config
        
    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")
        return None

def test_optimizer_initialization():
    """最適化クラスの初期化テスト"""
    print("\n" + "="*50)
    print("2. 最適化クラス初期化テスト")
    print("="*50)
    
    try:
        optimizer = KyoteiOptunaOptimizer()
        print("✅ 最適化クラス初期化成功")
        print(f"パラメータ数: {len(optimizer.param_ranges)}")
        print(f"試行回数: {optimizer.optimization_config['n_trials']}")
        
        return optimizer
        
    except Exception as e:
        print(f"❌ 最適化クラス初期化エラー: {e}")
        return None

def test_hyperparameter_suggestion():
    """ハイパーパラメータ提案テスト"""
    print("\n" + "="*50)
    print("3. ハイパーパラメータ提案テスト")
    print("="*50)
    
    try:
        optimizer = KyoteiOptunaOptimizer()
        
        # テスト用の研究を作成
        study = optuna.create_study(
            study_name="test_study",
            direction="maximize",
            storage=None  # インメモリ
        )
        
        # ハイパーパラメータ提案をテスト
        trial = study.ask()
        params = optimizer.suggest_hyperparameters(trial)
        
        print("✅ ハイパーパラメータ提案成功")
        print("提案されたパラメータ:")
        for param, value in params.items():
            print(f"  {param}: {value}")
        
        # パラメータの範囲チェック
        for param, value in params.items():
            config = optimizer.param_ranges[param]
            if config['type'] == 'float':
                min_val, max_val = config['range']
                if not (min_val <= value <= max_val):
                    print(f"⚠️  {param}: 範囲外の値 {value} (範囲: {min_val}-{max_val})")
            elif config['type'] == 'int':
                min_val, max_val = config['range']
                if not (min_val <= value <= max_val):
                    print(f"⚠️  {param}: 範囲外の値 {value} (範囲: {min_val}-{max_val})")
        
        return True
        
    except Exception as e:
        print(f"❌ ハイパーパラメータ提案エラー: {e}")
        return False

def test_study_creation():
    """研究作成テスト"""
    print("\n" + "="*50)
    print("4. 研究作成テスト")
    print("="*50)
    
    try:
        optimizer = KyoteiOptunaOptimizer()
        study = optimizer.create_study()
        
        print("✅ 研究作成成功")
        print(f"研究名: {study.study_name}")
        print(f"方向: {study.direction}")
        print(f"最適化対象: {optimizer.optimization_config['metric']}")
        
        return study
        
    except Exception as e:
        print(f"❌ 研究作成エラー: {e}")
        return None

def test_simple_optimization():
    """簡単な最適化テスト（1試行のみ）"""
    print("\n" + "="*50)
    print("5. 簡単な最適化テスト（1試行）")
    print("="*50)
    
    try:
        # 設定を簡略化
        optimizer = KyoteiOptunaOptimizer()
        optimizer.optimization_config['n_trials'] = 1
        optimizer.optimization_config['total_timesteps'] = 1000  # 短縮
        
        print("最適化を開始します...")
        print("（1試行のみ、1000ステップで短縮版）")
        
        # 最適化実行
        results = optimizer.run_optimization()
        
        print("✅ 最適化テスト成功")
        print(f"最適パラメータ: {results['best_params']}")
        print(f"最適値: {results['best_value']}")
        
        return results
        
    except Exception as e:
        print(f"❌ 最適化テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """メイン実行関数"""
    print("Optuna設定テスト開始")
    print(f"開始時刻: {datetime.now()}")
    
    # テスト実行
    tests = [
        ("設定ファイル読み込み", test_config_loading),
        ("最適化クラス初期化", test_optimizer_initialization),
        ("ハイパーパラメータ提案", test_hyperparameter_suggestion),
        ("研究作成", test_study_creation),
        ("簡単な最適化", test_simple_optimization)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "✅ 成功" if result else "❌ 失敗"
        except Exception as e:
            results[test_name] = f"❌ エラー: {e}"
    
    # 結果サマリー
    print("\n" + "="*50)
    print("テスト結果サマリー")
    print("="*50)
    
    for test_name, result in results.items():
        print(f"{test_name}: {result}")
    
    # 成功判定
    success_count = sum(1 for result in results.values() if "✅" in result)
    total_count = len(results)
    
    print(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 すべてのテストが成功しました！")
        print("Optuna設定は正常に動作しています。")
    else:
        print("⚠️ 一部のテストが失敗しました。")
        print("エラーの詳細を確認してください。")

if __name__ == "__main__":
    main() 