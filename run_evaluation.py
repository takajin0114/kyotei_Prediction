#!/usr/bin/env python3
"""
競艇予測システム - 評価スクリプト実行ラッパー
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """メイン実行関数"""
    print("競艇予測システム - 評価スクリプト")
    print("=" * 50)
    
    try:
        from kyotei_predictor.tools.evaluation.evaluate_graduated_reward_model import main as eval_main
        eval_main()
    except ImportError as e:
        print(f"エラー: 必要なモジュールが見つかりません: {e}")
        print("kyotei_predictor.tools.evaluation.evaluate_graduated_reward_model を確認してください")
        return 1
    except Exception as e:
        print(f"エラー: 評価実行中にエラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 