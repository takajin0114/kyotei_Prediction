# Legacy ディレクトリ

**最終更新日**: 2025-01-27

## 概要

このディレクトリには、開発過程で作成された古いバージョンのスクリプトや、現在は使用されていないが参考として保持しているファイルが含まれています。

## 内容

### 最適化スクリプト（古いバージョン）
- `optimize_202403.py` - 2024年3月データ用の古い最適化スクリプト
- `manual_optimization_202403.py` - 手動最適化スクリプト
- `simple_optimization_202403.py` - シンプル最適化スクリプト
- `run_optimization_*.py` - 各種実行スクリプト

### 分析スクリプト（古いバージョン）
- `analysis_202401_results.py` - 2024年1月結果分析
- `analysis_202401_results_colab.py` - Colab版分析スクリプト
- `performance_improvement_analysis.py` - パフォーマンス改善分析
- `reward_design_analysis.py` - 報酬設計分析

### 統合スクリプト（古いバージョン）
- `universal_integration.py` - 汎用統合スクリプト
- `colab_integration.py` - Colab統合スクリプト
- `colab_setup.py` - Colab設定スクリプト

## 注意事項

- これらのファイルは現在のシステムでは使用されていません
- 新しいバージョンは `optimization/` ディレクトリにあります
- 参考資料として保持していますが、削除しても問題ありません
- 必要に応じて新しいシステムに統合することも可能です

## 新しいバージョンへの移行

現在使用されている新しいバージョン：
- `kyotei_predictor/tools/optimization/optimize_graduated_reward.py` - 最新の最適化スクリプト
- `kyotei_predictor/tools/analysis/` - 最新の分析ツール
- `kyotei_predictor/utils/` - 統合ユーティリティ