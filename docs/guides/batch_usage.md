# 統合実行スクリプト使用ガイド

## 概要

競艇予測最適化の統合実行スクリプトの使い方です。スクリプトは **`scripts/`** にまとまっています。実行時はプロジェクトルートに自動で移動します。

## 利用可能なスクリプト（scripts/）

| ファイル | 説明 |
|----------|------|
| **run_optimization_config.bat** | `optimization_config.ini` に基づいて最適化（推奨） |
| **run_optimization_batch.bat** | 中速モード・20試行で即実行 |
| **run_optimization_simple.bat** | 簡易版・設定ファイル読み込み |
| **run_learning_prediction_cycle.bat** | 学習→予測を一括（test_raw） |
| **run_learning_prediction_cycle.sh** | 学習→予測を一括（test_raw, Linux/macOS向け） |
| **cleanup_old_files.bat** | 古いログ・Optuna ファイルの削除 |

## 実行方法

```bash
# プロジェクトルートから
scripts\run_optimization_config.bat
scripts\run_learning_prediction_cycle.bat
scripts\cleanup_old_files.bat

# Linux / macOS
./scripts/run_learning_prediction_cycle.sh

# または scripts フォルダ内でダブルクリック
```

## 最適化モード（optimization_config.ini）

- **fast**: 開発・テスト向け（約1〜1.5時間/20試行）
- **medium**: 推奨（約6〜7時間/20試行）
- **normal**: 本格運用（約60〜80時間/20試行）

## 出力先

- 最適化結果: `optuna_results/`
- ログ: `logs/`（ルート）、`kyotei_predictor/logs/`（学習・予測の詳細）
- モデル: `optuna_models/`

## トラブルシューティング

- `run_learning_prediction_cycle.sh` は `VENV_PATH`（既定: `.venv`）を自動で探して有効化します。存在しない場合はシステム Python を使用します。
- 依存不足の場合は事前に `pip install -r requirements.txt` を実行してください。
- `.bat` 系の設定はルートの `optimization_config.ini` を編集してください。

### Linux/macOS 向け `.sh` の上書き例

```bash
VENV_PATH=.venv-cycle YEAR_MONTH=2024-05 PREDICT_DATE=2024-05-01 ./scripts/run_learning_prediction_cycle.sh
```
