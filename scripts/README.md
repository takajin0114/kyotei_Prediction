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
| **fetch_one_race.bat** | **1R のみデータ取得（桐生 1日・1R・疎通確認用）** |
| **fetch_one_race.ps1** | **上記の PowerShell 版** |
| **run_fetch_one_race.py** | **1R 取得の Python ランチャー（どこからでも実行可）** |
| **fetch_reperiod.bat** | **期間を指定してデータ再取得（中身の日付・会場を編集して使用）** |
| **fetch_5years.bat** | **過去5年分（2021-01-01〜2026-02-14）を取得。欠けている分のみ（OVERWRITE=0）。** |
| **fetch_1month.bat** | **過去1か月分（2026年1月）を取得。欠けている分のみ。** |
| cleanup_old_files.bat | 古いログ・Optuna ファイルの削除 |

**実行例**（プロジェクトルートで）:
```bash
# 1R だけ取得（実行確認用）
# 方法A: エクスプローラーで scripts\fetch_one_race.bat をダブルクリック（日本語パスでも可）
# 方法B: Junction（C:\GDrive 等）経由で日本語パスを回避する場合は docs/guides/junction_setup.md を参照
# 方法C: プロジェクトフォルダでターミナルを開いてから
scripts\fetch_one_race.bat
# または PowerShell
.\scripts\fetch_one_race.ps1
# または Python ランチャー（venv 有効化後）
python scripts/run_fetch_one_race.py

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
