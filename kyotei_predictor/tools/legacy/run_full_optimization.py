#!/usr/bin/env python3
"""
2024年3月データでの本番想定最適化実行スクリプト
50試行、本番モードで実行
"""

import sys
import os
import time
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """本番想定の最適化実行"""
    
    print("=== 2024年3月データでの本番想定最適化開始 ===")
    print(f"実行開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # モジュールのインポート
        print("1. モジュールインポート...")
        from kyotei_predictor.tools.optimization.optimize_graduated_reward import optimize_graduated_reward
        print("   ✓ 最適化モジュールインポート成功")
        
        # 環境の確認
        print("2. 環境確認...")
        from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager
        env = KyoteiEnvManager(data_dir="kyotei_predictor/data/raw/2024-03")
        print(f"   ✓ データペア数: {len(env.pairs)}")
        
        # 本番想定のパラメータ
        n_trials = 50  # 50試行
        data_dir = "kyotei_predictor/data/raw/2024-03"
        study_name = "graduated_reward_optimization_202403_full"
        test_mode = False  # 本番モード
        resume_existing = False  # 新規スタディ
        
        print(f"3. 最適化パラメータ:")
        print(f"   試行回数: {n_trials}")
        print(f"   データディレクトリ: {data_dir}")
        print(f"   スタディ名: {study_name}")
        print(f"   テストモード: {test_mode}")
        print(f"   既存スタディ継続: {resume_existing}")
        
        # 最適化実行
        print("4. 最適化実行開始...")
        start_time = time.time()
        
        study = optimize_graduated_reward(
            n_trials=n_trials,
            study_name=study_name,
            data_dir=data_dir,
            test_mode=test_mode,
            resume_existing=resume_existing
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n=== 最適化完了 ===")
        print(f"実行時間: {execution_time/3600:.2f}時間")
        print(f"最良の試行: {study.best_trial.number}")
        print(f"最良のスコア: {study.best_value:.4f}")
        print(f"総試行数: {len(study.trials)}")
        
        # 最良パラメータの表示
        print(f"\n最良のパラメータ:")
        for key, value in study.best_params.items():
            print(f"  {key}: {value}")
        
        return study
        
    except Exception as e:
        print(f"最適化実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()