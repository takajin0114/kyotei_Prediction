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
| **fetch_one_race.bat** | 1R のみデータ取得（桐生 1日・1R・疎通確認用） |
| **run_fetch_one_race.py** | 1R 取得の Python ランチャー（推奨） |
| **run_fetch_5year_chunked.sh** | 5年分を数回に分けて取得（進捗確認・次に取るNヶ月・指定期間）。venv自動使用。 |
| **run_batch_fetch_1month.sh** | 1ヶ月分取得（YYYY-MM 指定可）。venv自動使用。 |
| **fetch_5year_plan.json** | **5年分取得の対象月一覧（2021-01〜2026-02）。** |
| check_batch_fetch_stuck.sh | バッチ取得のスタック検知（ログ・プロセス監視） |
| cleanup_old_files.bat | 古いログ・Optuna ファイルの削除 |

**削除済み（.sh または Python で代替）**: fetch_1month.bat, fetch_5years.bat, fetch_reperiod.bat → 1ヶ月は `run_batch_fetch_1month.sh`、期間・5年は `run_fetch_5year_chunked.sh` または `python -m kyotei_predictor.tools.batch.fetch_5year_chunked` を使用。

**実行例**（プロジェクトルートで）:
```bash
# 1R だけ取得（実行確認用）
# 方法A: エクスプローラーで scripts\fetch_one_race.bat をダブルクリック（日本語パスでも可）
# 方法B: Junction（C:\GDrive 等）経由で日本語パスを回避する場合は docs/guides/junction_setup.md を参照
# 方法C: プロジェクトフォルダでターミナルを開いてから
scripts\fetch_one_race.bat
# または Python ランチャー（venv 有効化後・推奨）
python scripts/run_fetch_one_race.py

scripts\run_optimization_config.bat
scripts\run_learning_prediction_cycle.bat

# Linux / macOS
./scripts/run_learning_prediction_cycle.sh

# Linux / macOS（環境変数で上書き）
VENV_PATH=.venv-cycle YEAR_MONTH=2024-05 PREDICT_DATE=2024-05-01 ./scripts/run_learning_prediction_cycle.sh

# Colab（Driveマウント済み想定）
python scripts/run_colab_learning_cycle.py --drive-root /content/drive/MyDrive/kyotei_prediction --year-month 2024-05 --minimal --predict-date 2024-05-01

# 1ヶ月分取得（最適化オプション）
python -m kyotei_predictor.tools.batch.batch_fetch_all_venues \
  --start-date 2026-01-01 --end-date 2026-01-31 --stadiums ALL \
  --output-data-dir kyotei_predictor/data/raw --overwrite \
  --rate-limit 1 --race-workers 6 --quiet

# 1ヶ月分取得（venv自動使用・activate不要）
./scripts/run_batch_fetch_1month.sh                     # 今月
./scripts/run_batch_fetch_1month.sh 2026-02             # 指定月
RACE_WORKERS=8 ./scripts/run_batch_fetch_1month.sh 2026-02

# 5年分を数回に分けて取得（過不足なく・venv自動使用）
./scripts/run_fetch_5year_chunked.sh check              # 進捗確認
./scripts/run_fetch_5year_chunked.sh next 1              # 未取得の次の1ヶ月
./scripts/run_fetch_5year_chunked.sh next 3              # 未取得の次の3ヶ月
./scripts/run_fetch_5year_chunked.sh range 2023-01-01 2023-12-31  # 指定期間
# または Python から
python -m kyotei_predictor.tools.batch.fetch_5year_chunked --check
python -m kyotei_predictor.tools.batch.fetch_5year_chunked --next 1
```

**データ取得の最適化オプション**:
- `--rate-limit 1`: リクエスト間の待機秒数（0.5〜1.0推奨。相手サイト負荷に配慮）
- `--race-workers 6`: レース取得の並列数（増やすと速いがサーバ負荷に注意）
- `--quiet` / `-q`: 進捗出力を抑制（エラーとサマリのみ表示）

**5年分を数回に分けて取得する手順**: [docs/guides/fetch_5year_chunked.md](../docs/guides/fetch_5year_chunked.md)

詳細: [docs/guides/batch_usage.md](../docs/guides/batch_usage.md)
