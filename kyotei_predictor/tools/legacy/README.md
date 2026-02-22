# legacy/ - 参照用コード（本番未使用）

このディレクトリには、**本番では使用しない**旧コード・Colab連携スクリプトを格納しています。

## ⚠️ 注意

- **本番運用・メインの学習・予測では使用しない**
- 参照・互換性確保のためのみ保持
- 新機能の開発時は **tools/optimization/**（optimize_graduated_reward）、**tools/ai/**（optuna_optimizer）、**tools/batch/**（batch_fetch_all_venues, train_*）を参照すること
- 実行する場合はプロジェクトルートで `python -m ...` を使うことを推奨（`sys.path.append` に依存しない）

## 📁 主な内容

| 種別 | 説明 |
|------|------|
| 旧最適化 | 2024年3月版（optimize_202403.py 等）。本流は tools/optimization/optimize_graduated_reward.py |
| Colab連携 | colab_integration.py, colab_setup.py |
| 過去の分析 | analysis_202401_results*.py 等 |

詳細は各ファイルの docstring を参照してください。
