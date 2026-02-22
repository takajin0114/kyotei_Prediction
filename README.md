# 競艇予測システム (Kyotei Prediction System)

## 概要

3連単予測を対象とした機械学習/RL ベースの予測システムです。  
主に以下のサイクルで運用します。

1. データ取得
2. 学習（最適化を含む）
3. 予測

## クイックスタート

### Windows

```bash
scripts\run_learning_prediction_cycle.bat
```

### Linux / macOS

```bash
./scripts/run_learning_prediction_cycle.sh
```

環境変数で実行条件を上書きする例:

```bash
VENV_PATH=.venv-cycle YEAR_MONTH=2024-05 PREDICT_DATE=2024-05-01 ./scripts/run_learning_prediction_cycle.sh
```

## 主要スクリプト（scripts/）

| スクリプト | 用途 |
|------------|------|
| `run_optimization_config.bat` | 最適化（`optimization_config.ini` 参照） |
| `run_optimization_batch.bat` | 最適化（中速・20試行） |
| `run_optimization_simple.bat` | 最適化（簡易版） |
| `run_learning_prediction_cycle.bat` | 学習→予測一括（Windows） |
| `run_learning_prediction_cycle.sh` | 学習→予測一括（Linux/macOS） |
| `fetch_one_race.bat` | 1R のみデータ取得（疎通確認用） |
| `fetch_reperiod.bat` | 期間指定でデータ再取得 |
| `fetch_5years.bat` | 過去5年分のデータ取得 |
| `cleanup_old_files.bat` | 古いログやOptuna成果物の整理 |

一覧・詳細: [scripts/README.md](scripts/README.md)

## 安全な Git 運用（重要）

このリポジトリは LFS 対象ファイルが多く、環境によっては `git status` に大量の `M` が出る場合があります。  
誤コミット防止のため、次を徹底してください。

- `git add .` は使わず、**対象ファイルを明示して add**
- `git diff --cached --name-only` でコミット対象を確認
- 意図しないステージは `git restore --staged <path>` で解除

詳細: [docs/guides/git_staging_safety.md](docs/guides/git_staging_safety.md)

## ドキュメント

- [docs/README.md](docs/README.md): ドキュメント全体の入口
- **[docs/guides/processing_flow.md](docs/guides/processing_flow.md): 処理の流れ（Cursorで取得・保管 → Colabで学習 → Cursorで取得・予測）**
- [docs/PROJECT_LAYOUT.md](docs/PROJECT_LAYOUT.md): ディレクトリ構成
- [docs/guides/batch_usage.md](docs/guides/batch_usage.md): 実行スクリプトの使い方
- [docs/guides/google_drive_colab_workflow.md](docs/guides/google_drive_colab_workflow.md): Google Drive保存とColab学習の手順
- [docs/guides/git_staging_safety.md](docs/guides/git_staging_safety.md): 大量変更時の安全なステージング運用
- [docs/LEARNING_AND_PREDICTION_STATUS.md](docs/LEARNING_AND_PREDICTION_STATUS.md): 学習/予測の現状

## セットアップ

```bash
python -m venv venv
pip install -r requirements.txt
```

Windows で仮想環境を有効化する場合:

```bash
.\venv\Scripts\Activate.bat
```

Linux/macOS の場合:

```bash
source venv/bin/activate
```
