# scripts/

実行用スクリプト（Windows `.bat` / Linux `.sh`）をまとめたディレクトリです。いずれも実行時にプロジェクトルートへ移動してから処理します。

| ファイル | 説明 |
|----------|------|
| run_optimization_config.bat | 最適化（optimization_config.ini 参照・推奨） |
| run_optimization_batch.bat | 最適化（中速・20試行で即実行） |
| run_optimization_simple.bat | 最適化（簡易版） |
| run_learning_prediction_cycle.bat | 学習→予測一括（test_raw） |
| run_learning_prediction_cycle.sh | 学習→予測一括（test_raw, Linux/macOS向け） |
| run_colab_learning_cycle.py | Google Drive上データで学習/予測（Colab向け） |
| cleanup_old_files.bat | 古いログ・Optuna ファイルの削除 |

**実行例**（プロジェクトルートで）:
```bash
scripts\run_optimization_config.bat
scripts\run_learning_prediction_cycle.bat

# Linux / macOS
./scripts/run_learning_prediction_cycle.sh

# Linux / macOS（環境変数で上書き）
VENV_PATH=.venv-cycle YEAR_MONTH=2024-05 PREDICT_DATE=2024-05-01 ./scripts/run_learning_prediction_cycle.sh

# Colab（Driveマウント済み想定）
python scripts/run_colab_learning_cycle.py --drive-root /content/drive/MyDrive/kyotei_prediction --year-month 2024-05 --minimal --predict-date 2024-05-01
```

詳細: [docs/guides/batch_usage.md](../docs/guides/batch_usage.md)
