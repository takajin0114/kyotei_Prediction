#!/usr/bin/env python3
"""
2024年3月データを使用した最適化テストスクリプト
"""

import subprocess
import sys
import os
from datetime import datetime

def test_optimization():
    """最適化のテスト実行"""
    print("=== 2024年3月データ最適化テスト開始 ===")
    print(f"開始時刻: {datetime.now()}")
    
    # テスト用の設定
    data_dir = "kyotei_predictor/data/raw/2024-03"
    n_trials = 3  # テスト用に少ない試行回数
    study_name = "test_202403_optimization"
    
    # コマンド構築
    cmd = [
        sys.executable, "-m", "kyotei_predictor.tools.optimization.optimize_graduated_reward",
        "--data-dir", data_dir,
        "--study-name", study_name,
        "--n-trials", str(n_trials),
        "--test-mode"  # テストモードで短時間実行
    ]
    
    print(f"実行コマンド: {' '.join(cmd)}")
    print(f"データディレクトリ: {data_dir}")
    print(f"試行回数: {n_trials}")
    print(f"スタディ名: {study_name}")
    
    try:
        # 最適化実行
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30分タイムアウト
        
        print(f"\n=== 実行結果 ===")
        print(f"終了コード: {result.returncode}")
        print(f"標準出力:")
        print(result.stdout)
        
        if result.stderr:
            print(f"エラー出力:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ 最適化テスト成功")
        else:
            print("❌ 最適化テスト失敗")
            
    except subprocess.TimeoutExpired:
        print("❌ タイムアウト: 30分以内に完了しませんでした")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    print(f"\n終了時刻: {datetime.now()}")

if __name__ == "__main__":
    test_optimization()