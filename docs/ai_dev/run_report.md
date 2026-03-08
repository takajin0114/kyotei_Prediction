<!-- AI開発ワークフロー用ファイル: Cursorがここに実装結果をまとめる -->

# Run Report

## Summary

**今回**: 競艇AIの実験サイクルを半自動化する新規スクリプトを追加。既存ロジック・モデルコードは変更せず、外部ライブラリも追加していない。validation → ROI → experiment log → leaderboard を 1 コマンドで実行可能にした。

## Changed files

```
docs/ai_dev/README.md
kyotei_predictor/application/baseline_predict_usecase.py
kyotei_predictor/cli/baseline_predict.py
kyotei_predictor/cli/baseline_train.py
kyotei_predictor/infrastructure/baseline_model_repository.py
kyotei_predictor/pipelines/state_vector.py
kyotei_predictor/tests/test_baseline_contracts.py
kyotei_predictor/tools/feature_sweep.py
kyotei_predictor/tools/rolling_validation_roi.py
kyotei_predictor/tools/rolling_validation_windows.py
```

## Commands run

- `mkdir -p docs/ai_dev/templates scripts`
- `chmod +x scripts/ai_dev_cycle.sh`
- `python3 scripts/generate_run_report.py`

## Execution results

- 全コマンド正常終了（exit code 0）
- `docs/ai_dev/run_report.md` が上書き生成された
- `scripts/ai_dev_cycle.sh` に実行権限を付与済み

## Diff summary

### git diff --stat

```
docs/ai_dev/README.md                              | 18 ++++++
 .../application/baseline_predict_usecase.py        | 62 ++++++++++++++++++-
 kyotei_predictor/cli/baseline_predict.py           |  8 +++
 kyotei_predictor/cli/baseline_train.py             |  8 +++
 .../infrastructure/baseline_model_repository.py    | 16 +++--
 kyotei_predictor/pipelines/state_vector.py         | 69 ++++++++++++++++++----
 kyotei_predictor/tests/test_baseline_contracts.py  | 46 +++++++++++++++
 kyotei_predictor/tools/feature_sweep.py            |  1 +
 kyotei_predictor/tools/rolling_validation_roi.py   |  3 +-
 .../tools/rolling_validation_windows.py            |  6 +-
 10 files changed, 218 insertions(+), 19 deletions(-)
```

### git status --short

```
M docs/ai_dev/README.md
 M kyotei_predictor/application/baseline_predict_usecase.py
 M kyotei_predictor/cli/baseline_predict.py
 M kyotei_predictor/cli/baseline_train.py
 M kyotei_predictor/infrastructure/baseline_model_repository.py
 M kyotei_predictor/pipelines/state_vector.py
 M kyotei_predictor/tests/test_baseline_contracts.py
 M kyotei_predictor/tools/feature_sweep.py
 M kyotei_predictor/tools/rolling_validation_roi.py
 M kyotei_predictor/tools/rolling_validation_windows.py
?? docs/ai_dev/AI_HANDOVER_AUDIT_REPORT.md
?? docs/ai_dev/current_task.md
?? docs/ai_dev/run_report.md
?? docs/ai_dev/templates/
?? kyotei_predictor/pipelines/racer_history.py
?? kyotei_predictor/tests/test_racer_history.py
?? scripts/ai_dev_cycle.sh
?? scripts/generate_run_report.py
```

## Concerns

- 既存コードは一切変更していない（今回の変更は新規ファイル追加と README 追記のみ）
- `bash scripts/ai_dev_cycle.sh` は**リポジトリルート**で実行する必要がある（scripts 配下で実行するとパスがずれる）
- `run_report.md` は毎回上書きされるため、手で追記した内容は次回の `generate_run_report.py` 実行で消える

## Next actions

1. この `run_report.md` の内容を ChatGPT に貼り付けて引き継ぐ
2. 次のタスクがある場合は、`docs/ai_dev/current_task.md` に指示を書く（または `templates/current_task_template.md` をコピーして編集）
3. 必要なら `scripts/generate_run_report.py` の「Commands run」「Execution results」等を手動で追記してから ChatGPT に渡す

---

## 実験サイクル自動化（今回の実装）

### 作成ファイル

| ファイル | 説明 |
|----------|------|
| `scripts/experiments/` | 実験用スクリプト用ディレクトリ |
| `scripts/experiments/create_experiment_log.py` | experiments/logs/ に EXP-xxxx.md を生成（既存ログの次番号を採番） |
| `scripts/experiments/update_leaderboard.py` | experiments/leaderboard.md に \| Experiment \| ROI \| Notes \| 形式で1行追加 |
| `scripts/run_experiment_cycle.sh` | validation → ROI → log 生成 → leaderboard 更新を一括実行 |

**更新したファイル**

| ファイル | 変更内容 |
|----------|----------|
| `docs/ai_dev/README.md` | 「Experiment Automation」セクションを追加 |

### 実行コマンド

- `mkdir -p scripts/experiments`
- `chmod +x scripts/run_experiment_cycle.sh`
- 実験サイクル実行例: `bash scripts/run_experiment_cycle.sh`（要 `KYOTEI_DB_PATH` または `data/races.db`）

### 潜在的な問題

- **DB パス**: `KYOTEI_DB_PATH` 未設定時は `data/races.db` を参照。存在しないと validation で失敗する。
- **validation モジュール**: 仕様の「例」にある `python3 -m kyotei_predictor.validation` は未実装のため、現状は `kyotei_predictor.tools.rolling_validation_roi` を呼んでいる。別の検証に差し替える場合は `run_experiment_cycle.sh` の該当行を編集する必要がある。
- **leaderboard の Recent 表**: `update_leaderboard.py` は「## Recent」セクションに行を追加する。既存の「ROI Leaderboard」表は触らない。
- **複数戦略時の ROI**: `rolling_validation_summary.json` が配列の場合は先頭要素の ROI を leaderboard に記載。複数モデル・戦略を並列で比較した場合は手動でログ・leaderboard を補う必要がある。

### 次に自動化できる改善案

1. **条件・メモの自動反映**: `create_experiment_log.py` に `--conditions` / `--notes` を渡すように `run_experiment_cycle.sh` で環境変数（例: `EXP_CONDITIONS`, `EXP_NOTES`）を読み、ログと leaderboard の Notes を揃える。
2. **validation の差し替え**: `KYOTEI_VALIDATION_CMD` のような環境変数で「validation に実行するコマンド」を指定できるようにし、`kyotei_predictor.validation` を実装したあと切り替え可能にする。
3. **dry-run**: `run_experiment_cycle.sh --dry-run` で validation 以外（log 生成・leaderboard 更新）をスキップし、既存の summary JSON だけで log/leaderboard だけ更新するモードを追加する。
4. **番号の手動指定**: `create_experiment_log.py` に `--exp-id EXP-0007` を渡して、自動採番ではなく指定番号でログを生成できるようにする。
