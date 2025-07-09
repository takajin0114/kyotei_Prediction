#!/usr/bin/env python3
"""
競艇予測システム - 学習スクリプト実行ラッパー
"""

import sys
import os
import argparse

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='競艇予測システム - 学習スクリプト')
    parser.add_argument('--mode', choices=['basic', 'extended'], default='basic',
                       help='学習モード: basic (基本学習) または extended (拡張学習)')
    parser.add_argument('--steps', type=int, default=None,
                       help='学習ステップ数 (extendedモードで使用)')
    
    args = parser.parse_args()
    
    print("競艇予測システム - 学習スクリプト")
    print("=" * 50)
    print(f"学習モード: {args.mode}")
    
    try:
        if args.mode == 'basic':
            from kyotei_predictor.tools.batch.train_graduated_reward import main as train_main
            train_main()
        elif args.mode == 'extended':
            from kyotei_predictor.tools.batch.train_extended_graduated_reward import main as train_main
            train_main()
    except ImportError as e:
        print(f"エラー: 必要なモジュールが見つかりません: {e}")
        if args.mode == 'basic':
            print("kyotei_predictor.tools.batch.train_graduated_reward を確認してください")
        else:
            print("kyotei_predictor.tools.batch.train_extended_graduated_reward を確認してください")
        return 1
    except Exception as e:
        print(f"エラー: 学習実行中にエラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 