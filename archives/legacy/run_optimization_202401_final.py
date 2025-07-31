#!/usr/bin/env python3
"""
2024年1月データでの段階的報酬最適化実行スクリプト（最終版）
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
        print("=== 2024年1月データでの段階的報酬最適化 ===")
        
        # データディレクトリの確認
        data_dir = "kyotei_predictor/data/raw/2024-01"
        if not os.path.exists(data_dir):
            print(f"❌ データディレクトリが存在しません: {data_dir}")
            return None
        
        print(f"✅ データディレクトリ確認: {data_dir}")
        
        # モジュールのインポート
        try:
            from kyotei_predictor.tools.optimization.optimize_graduated_reward_202401 import optimize_graduated_reward_202401
            print("✅ モジュール読み込み成功")
        except ImportError as e:
            print(f"❌ モジュール読み込みエラー: {e}")
            return None
        
        # 最適化実行
        print("\n最適化を開始します...")
        result = optimize_graduated_reward_202401(
            n_trials=50,  # 本番想定で50試行
            study_name="graduated_reward_optimization_202401",
            data_dir=data_dir,
            test_mode=False  # 本番モード
        )
        
        if result is None:
            print("❌ 最適化が失敗しました")
            return None
        
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