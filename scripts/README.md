# scripts/

実行用バッチファイルをまとめたディレクトリです。いずれも実行時にプロジェクトルートへ移動してから処理します。

| ファイル | 説明 |
|----------|------|
| run_optimization_config.bat | 最適化（optimization_config.ini 参照・推奨） |
| run_optimization_batch.bat | 最適化（中速・20試行で即実行） |
| run_optimization_simple.bat | 最適化（簡易版） |
| run_learning_prediction_cycle.bat | 学習→予測一括（test_raw） |
| cleanup_old_files.bat | 古いログ・Optuna ファイルの削除 |

**実行例**（プロジェクトルートで）:
```bash
scripts\run_optimization_config.bat
scripts\run_learning_prediction_cycle.bat
```

詳細: [docs/guides/batch_usage.md](../docs/guides/batch_usage.md)
