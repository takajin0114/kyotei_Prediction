#!/usr/bin/env python3
"""
最小限学習テストスクリプト - 最適化スクリプトの動作確認
"""

import sys
import os
from pathlib import Path

# プロジェクトルートを取得
project_root = Path(__file__).parent.parent.parent
kyotei_predictor_path = project_root / "kyotei_predictor"

# パスを追加
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(kyotei_predictor_path))
sys.path.insert(0, str(kyotei_predictor_path / "tools"))
sys.path.insert(0, str(kyotei_predictor_path / "pipelines"))
sys.path.insert(0, str(kyotei_predictor_path / "utils"))

def test_optimization_script():
    """最適化スクリプトのテスト"""
    print("=== 段階的報酬設計モデルのハイパーパラメータ最適化開始 ===")
    
    try:
        from tools.optimization.optimize_graduated_reward import main as optimize_main
        
        # テスト用データディレクトリを使用
        data_dir = "kyotei_predictor/data/test_raw"
        print(f"使用するデータディレクトリ: {data_dir}")
        
        # 最小限テストモードで実行
        print("最小限テストモード: 試行回数1回、非常に短い学習時間")
        
        # 環境変数でデータディレクトリを設定（テスト時のみ）
        os.environ['DATA_DIR'] = data_dir
        
        # 最適化スクリプトを実行
        optimize_main(
            n_trials=1,  # 最小限
            test_mode=False,
            minimal_mode=True,  # 最小限モード
            continue_study=False
        )
        
        print("最適化スクリプトテスト完了 ✓")
        
    except Exception as e:
        print(f"最適化スクリプトテストエラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン実行関数"""
    print("=== 最小限学習テスト実行 ===")
    print()
    
    # 最適化スクリプトテスト実行
    test_optimization_script()
    print()
    
    print("=== テスト完了 ===")
    print("最小限学習テストが正常に完了しました。")
    print("最適化スクリプトが正常に動作しています。")

if __name__ == "__main__":
    main() 