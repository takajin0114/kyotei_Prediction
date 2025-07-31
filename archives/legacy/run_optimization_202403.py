#!/usr/bin/env python3
"""
2024年3月データでの段階的報酬最適化実行スクリプト
"""

import sys
import os
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """メイン実行関数"""
    try:
        print("=== 2024年3月データでの段階的報酬最適化 ===")
        
        # モジュールのインポート
        from kyotei_predictor.tools.optimization.optimize_graduated_reward import optimize_graduated_reward
        
        print("モジュール読み込み成功")
        
        # 最適化実行
        print("\n最適化を開始します...")
        result = optimize_graduated_reward(
            n_trials=3,  # 3試行でテスト
            study_name="test_202403_graduated_reward",
            data_dir="kyotei_predictor/data/raw/2024-03",
            test_mode=True
        )
        
        print(f"\n✅ 最適化完了")
        print(f"最良の試行: {result.best_trial.number}")
        print(f"最良のスコア: {result.best_value:.4f}")
        print(f"総試行数: {len(result.trials)}")
        
        return result
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main() 