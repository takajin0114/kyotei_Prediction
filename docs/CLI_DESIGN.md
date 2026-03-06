# Python CLI 実行設計

OS 非依存実行のための CLI 設計と最小導線の説明。詳細な運用方針は `OS_PORTABILITY_STRATEGY.md` を参照。

---

## 目標構造

| エントリポイント | 役割 |
|------------------|------|
| `python -m kyotei_predictor.cli.optimize` | 最適化（optimization_config.ini + override） |
| `python -m kyotei_predictor.cli.predict` | 予測（prediction_tool へ転送） |
| `python -m kyotei_predictor.cli.verify` | 検証（EVALUATION_MODE を config から反映） |
| `python -m kyotei_predictor.cli.report` | 検証・予測サマリ（簡易ダッシュボード） |

---

## 設定

- **中心となる設定ファイル**: ルートの `optimization_config.ini`
- **主なキー**: MODE, TRIALS, YEAR_MONTH, EVALUATION_MODE, VENV_PATH, LOG_DIR, CLEANUP_DAYS
- **CLI 共通**
  - `--config <path>`: ini のパス（未指定時はカレントの `optimization_config.ini`）
  - 各サブコマンドで override 引数により config を上書き可能

---

## 各 CLI のインターフェース（最小）

### cli.optimize

- `--config` / `--n-trials` / `--mode` (fast|medium|normal) / `--year-month`
- config を読み、既存の `kyotei_predictor.tools.optimization.optimize_graduated_reward` に渡す。
- 設定ローダー: `kyotei_predictor.cli.config_loader.load_optimization_config`

### cli.predict

- `--config`（将来の DATA_DIR 等の読込用）、それ以外は `prediction_tool` にそのまま転送（`--predict-date`, `--venues` 等）。

### cli.verify

- `--config` / `--prediction` / `--data-dir` / `--evaluation-mode` / `--output` / `--save` / `--verbose`
- config の EVALUATION_MODE を `--evaluation-mode` に反映し、`kyotei_predictor.tools.verify_predictions` を実行。

### cli.report

- `--project-root` / `--format` (markdown|json)
- `scripts/summarize_verification_results.run(project_root, format)` を呼び出し。

---

## ディレクトリ構成（CLI まわり）

```
kyotei_predictor/
  cli/
    __init__.py
    config_loader.py   # optimization_config.ini の KEY=VALUE 読込
    optimize.py        # 最適化エントリ
    predict.py         # 予測エントリ（転送）
    verify.py          # 検証エントリ
    report.py          # サマリエントリ
```

---

## TODO（将来の完全 CLI 化）

- [ ] 学習→予測→検証を一括実行する `--run-cycle` のようなオプションを cli に追加
- [ ] cleanup・実行時間計測を Python 側に移行し、scripts をさらに薄くする
- [ ] `check_batch_fetch_stuck` / `cleanup_old_files` のロジックを Python ツール化（任意）
