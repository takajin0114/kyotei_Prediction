# 最適化スクリプト使用ガイド

## 概要

最適化は **`scripts/run_optimization_config.bat`**（設定ファイルベース）または **`scripts/run_optimization_batch.bat`** で実行します。設定はルートの `optimization_config.ini` で行います。

## 前提条件

- Python 3.8+
- プロジェクトルートに `optimization_config.ini`, `requirements.txt` があること
- データ: `kyotei_predictor/data/raw/` または `--data-dir` で指定

## 実行方法

```bash
# プロジェクトルートから
scripts\run_optimization_config.bat
```

## 設定 (optimization_config.ini)

| 項目 | 説明 |
|------|------|
| MODE | fast / medium / normal |
| TRIALS | 試行回数 |
| YEAR_MONTH | 対象年月 (YYYY-MM) |
| VENV_PATH | 仮想環境 (venv) |
| LOG_DIR | ログ出力先 (logs) |
| CLEANUP_DAYS | 古いファイル削除の日数 |

## 出力

- ログ: `logs/optimization_*.log`
- 結果: `optuna_results/`, `optuna_models/`, `optuna_studies/`, `optuna_logs/`

## トラブルシューティング

- 仮想環境: バッチが自動作成
- 依存: `pip install -r requirements.txt`
- データ不足: `kyotei_predictor/data/raw/` に race_data_* と odds_data_* のペアを配置

詳細は [batch_usage.md](batch_usage.md) を参照。
