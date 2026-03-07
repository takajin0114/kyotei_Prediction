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

## Reproducibility Diagnostics

このリポジトリでは以下の診断ツールを実装しています。

- **compare_run_summaries** — 2 回の run の summary JSON を比較し、差分を表示
- **train_file_manifest** — 学習に使ったファイル一覧・hash（JSON 経路時）
- **verify_details** — 検証の前提条件・スキップ理由・レース別詳細

再現性確認手順:

1. 同一条件で runA / runB を実行（`--db-path` 指定で DB 統一推奨）
2. `compare_run_summaries` で 2 つの summary を比較
3. sample_mode の違い（head / random / all）で比較

詳細は [docs/REPRODUCIBILITY_DIAGNOSIS.md](docs/REPRODUCIBILITY_DIAGNOSIS.md) を参照してください。

## Model Comparison

現在比較しているモデル:

- sklearn baseline
- LightGBM
- XGBoost

評価方法:

- rolling validation
- ROI（mean / median / std / overall）
- log loss
- Brier score

詳細: [docs/MODEL_COMPARISON.md](docs/MODEL_COMPARISON.md)

## ドキュメント

- **[docs/README.md](docs/README.md)**: ドキュメント全体の**索引（推奨入口）**。目的別にリンク一覧あり。
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

## テスト

プロジェクトルートで実行（仮想環境 `.venv` を使う場合）:

```bash
.venv/bin/python -m pytest kyotei_predictor/tests/ -v --tb=short
```

仮想環境を有効化している場合は `pytest kyotei_predictor/tests/` でも可。

**実行手順・メインのみの実行・除外オプションなど**  
→ [kyotei_predictor/tests/README_TESTS.md](kyotei_predictor/tests/README_TESTS.md)

## ドキュメント・構成

- **ドキュメント入口**: [docs/README.md](docs/README.md)
- **実験管理**: [experiments/](experiments/)
- **分析・Colab ノートブック**: [notebooks/](notebooks/)（Colab 用は `notebooks/colab/`）
- **新規 AI セッション開始時**: [docs/ai_dev/chat_bootstrap_prompt.md](docs/ai_dev/chat_bootstrap_prompt.md) を読む

## AI Development System

This project uses AI-assisted development.

- **Experiment tracking** is stored under [experiments/](experiments/).
- Before proposing new experiments, the AI should review [leaderboard](experiments/leaderboard.md) and [open questions](experiments/open_questions.md).

Before starting a new development session, the AI should read:

- [docs/ai_dev/project_status.md](docs/ai_dev/project_status.md)
- [docs/ai_dev/next_tasks.md](docs/ai_dev/next_tasks.md)
- [docs/ai_dev/architecture.md](docs/ai_dev/architecture.md)
- [docs/ai_dev/experiment_log.md](docs/ai_dev/experiment_log.md)
