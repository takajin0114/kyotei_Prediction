# 統合バッチファイル使用ガイド

## 概要

競艇予測最適化の統合バッチの使い方です。バッチは **`scripts/`** にまとまっています。実行時はプロジェクトルートに自動で移動します。

## 利用可能なバッチ（scripts/）

| ファイル | 説明 |
|----------|------|
| **run_optimization_config.bat** | `optimization_config.ini` に基づいて最適化（推奨） |
| **run_optimization_batch.bat** | 中速モード・20試行で即実行 |
| **run_optimization_simple.bat** | 簡易版・設定ファイル読み込み |
| **run_learning_prediction_cycle.bat** | 学習→予測を一括（test_raw） |
| **cleanup_old_files.bat** | 古いログ・Optuna ファイルの削除 |

## 実行方法

```bash
# プロジェクトルートから
scripts\run_optimization_config.bat
scripts\run_learning_prediction_cycle.bat
scripts\cleanup_old_files.bat

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

- 仮想環境がない場合: バッチが `venv` を自動作成します
- 依存不足: `pip install -r requirements.txt` をバッチが実行します
- 設定: ルートの `optimization_config.ini` を編集してください
