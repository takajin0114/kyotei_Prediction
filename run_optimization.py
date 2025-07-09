#!/usr/bin/env python3
"""
競艇予測システム - 最適化スクリプト実行ラッパー
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """メイン実行関数"""
    print("競艇予測システム - 最適化スクリプト")
    print("=" * 50)
    
    try:
        from kyotei_predictor.tools.optimization.optimize_graduated_reward import main as opt_main
        opt_main()
    except ImportError as e:
        print(f"エラー: 必要なモジュールが見つかりません: {e}")
        print("kyotei_predictor.tools.optimization.optimize_graduated_reward を確認してください")
        return 1
    except Exception as e:
        print(f"エラー: 最適化実行中にエラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 