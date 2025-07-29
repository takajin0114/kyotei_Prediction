#!/usr/bin/env python3
"""
汎用最適化実行スクリプト
任意の期間のデータでハイパーパラメータ最適化を実行
"""

import sys
import os
import argparse
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append('.')

def validate_data_directory(data_dir):
    """データディレクトリの存在確認"""
    if not os.path.exists(data_dir):
        raise ValueError(f"データディレクトリが存在しません: {data_dir}")
    
    # レースデータとオッズデータの存在確認
    race_files = [f for f in os.listdir(data_dir) if f.startswith('race_data_')]
    odds_files = [f for f in os.listdir(data_dir) if f.startswith('odds_data_')]
    
    if not race_files or not odds_files:
        raise ValueError(f"データファイルが見つかりません: {data_dir}")
    
    print(f"データ確認完了: {len(race_files)}個のレースファイル, {len(odds_files)}個のオッズファイル")
    return True

def run_optimization(data_dir, n_trials=20, test_mode=False, study_name=None):
    """最適化実行"""
    from kyotei_predictor.tools.optimization.optimize_graduated_reward import optimize_graduated_reward
    
    # データディレクトリの検証
    validate_data_directory(data_dir)
    
    # スタディ名の自動生成
    if study_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode = "test" if test_mode else "full"
        study_name = f"optimization_{mode}_{timestamp}"
    
    print(f"=== 最適化開始 ===")
    print(f"データディレクトリ: {data_dir}")
    print(f"試行回数: {n_trials}")
    print(f"テストモード: {test_mode}")
    print(f"スタディ名: {study_name}")
    
    # 最適化実行
    study = optimize_graduated_reward(
        n_trials=n_trials,
        study_name=study_name,
        data_dir=data_dir,
        test_mode=test_mode
    )
    
    print(f"=== 最適化完了 ===")
    print(f"最良の試行: {study.best_trial.number}")
    print(f"最良のスコア: {study.best_value:.4f}")
    print(f"総試行数: {len(study.trials)}")
    
    return study

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="汎用最適化実行スクリプト")
    parser.add_argument('--data-dir', type=str, required=True,
                       help='データディレクトリのパス (例: kyotei_predictor/data/raw/2024-03)')
    parser.add_argument('--n-trials', type=int, default=20,
                       help='試行回数 (デフォルト: 20)')
    parser.add_argument('--test-mode', action='store_true',
                       help='テストモード（短時間設定）')
    parser.add_argument('--study-name', type=str, default=None,
                       help='Optunaスタディ名（自動生成される場合は指定不要）')
    
    args = parser.parse_args()
    
    try:
        study = run_optimization(
            data_dir=args.data_dir,
            n_trials=args.n_trials,
            test_mode=args.test_mode,
            study_name=args.study_name
        )
        
        print("最適化が正常に完了しました。")
        return study
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()