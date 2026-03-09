# Chat Context

## Generated At
2026-03-09

## Repository
kyotei_Prediction

## Run Report

<!-- AI開発ワークフロー用ファイル: Cursorがここに実装結果をまとめる -->

# Run Report

## Summary

Generated at: 2026-03-09. EXP-0006 正式 reference（top_n=6, ev=1.05）周辺の局所最適化を実施。top_n=6 固定で ev 再探索の結果 **ev=1.00 が最良**（-18.78%）→ adopt。ドキュメント整合性回復（暫定 best / 正式 reference の区別、bet sizing 正式表の追加）。

## Changed files

```
scripts/exp0006_local_opt_topn6_ev105.py
experiments/logs/EXP-0006_strategy_grid.md
experiments/leaderboard.md
docs/ai_dev/project_status.md
docs/ai_dev/chat_context.md
```

## Commands run

```bash
python3 scripts/exp0006_local_opt_topn6_ev105.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42
```

## Execution results

- Task1 (top_n=6 固定 ev sweep [1.00,1.02,1.05,1.07,1.10]): 最良 **ev=1.00 → -18.78%**（1.05:-19.71%, 1.07:-19.63%）
- Task2 (ev=1.05 固定 top_n [5,6,7]): 最良 top_n=6 → -19.71%
- Task3 (bet sizing, 最良条件 top_n=6 ev=1.00): fixed -18.78%, half_kelly -96.79%, capped_0.02 -23.51%, capped_0.05 -47.70%
- 出力: outputs/exp0006_local_opt_topn6_ev105.json

## Diff summary

### git diff --stat

```
docs/ai_dev/README.md          | 18 ++++++++++++++++++
 docs/ai_dev/run_report.md      |  1 +
 scripts/ai_dev_cycle.sh        |  4 +++-
 scripts/generate_run_report.py |  2 +-
 4 files changed, 23 insertions(+), 2 deletions(-)
```

### git status --short

```
M docs/ai_dev/README.md
 M docs/ai_dev/run_report.md
 M scripts/ai_dev_cycle.sh
 M scripts/generate_run_report.py
?? docs/ai_dev/chat_context.md
?? scripts/generate_chat_context.py
```

## Concerns

(懸念点をここに記入)

## Next actions

(次アクション候補をここに記入。ChatGPT でレビューする場合は bash scripts/ai_dev_cycle.sh で chat_context.md を生成し raw URL を渡す。)

## Leaderboard

# Experiment Leaderboard

- **正式 reference (n_w=12)**: 同一条件・n_windows=12 で比較した公式結果。
- **暫定 best (n_w=4 等)**: 少ない window 数のみで未確定。採用前に n_w=12 再評価を要する。

| Rank | Experiment ID | Parameters | overall_roi_selected | Notes |
|---|---|---|---|---|
| 1 | EXP-0006 | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | **new reference**（正式 adopt） |
| 2 | EXP-0006 | top_n=6, ev=1.00 | **-18.78%** (n_w=12) | 正式 reference 周辺の局所最適（adopt） |
| 4 | EXP-0006 | top_n=3, ev=1.25 (grid) | -11.15% (n_w=4) | **暫定 best**（未確定） |
| 5 | EXP-0006 | top_n=6, ev=1.05 | -19.71% (n_w=12) | 正式 reference（top_n=6 系統・前回） |
| 6 | EXP-0005 | top_n=6, ev=1.20 | -20.7% (n_w=12) | 旧 reference |

Bet sizing 正式表は experiments/leaderboard.md の「Bet Sizing 比較」を参照。

## Notes

- EXP-0006: 正式 reference (n_w=12) 1位 top_n=3, ev=1.20（-14.88%）。2位 top_n=6, ev=1.00（-18.78%, 局所最適 adopt）。暫定 best (n_w=4) top_n=3, ev=1.25 は未確定。
- AI は新しい提案をする前に leaderboard を確認すること。

## Project Status

# Project Status

現在のプロジェクト状態。

- **メイン戦略**: Strategy B（XGBoost + sigmoid + top_n_ev）。**正式 reference (n_w=12)**: (1) 1位 **top_n=3, ev=1.20**（-14.88%, new reference adopt）。(2) 2位 **top_n=6, ev=1.00**（-18.78%, 正式 reference 周辺の局所最適 adopt）。暫定 best（n_w=4）の top_n=3, ev=1.25 は未確定。
- **データ**: DB を唯一の正（`kyotei_predictor/data/kyotei_races.sqlite`）。JSON 直読みは使わない。
- **評価**: rolling validation（n_windows=12）、extended_features、sigmoid calibration。extended_features_v2 は n12 正式比較で ROI 悪化のため hold。
- **特徴量セット**: train / predict / rolling validation / feature_sweep で **feature_set を明示引数**で指定可能。優先順位は「明示引数 > 環境変数 KYOTEI_FEATURE_SET > デフォルト」。学習時に使った feature_set は **meta.json に保存**され、予測時に不一致の場合は **warning** を出す。
  - `current_features` / `extended_features` / `extended_features_v2`
  - v2 は DB 由来の **recent_form**（直近N走の平均着順・1着率・3着内率）と **venue_course**（当該場成績）を実装済み。motor_trend・relative_race_strength は extended ベース。リーク防止のため「対象レース以前の履歴のみ」使用。
- **モデル比較**: sklearn / LightGBM / XGBoost を rolling validation で比較可能。EXP-0005 で XGBoost が最良 ROI（-20.7%）。LightGBM/XGBoost は環境に libomp が必要（brew install libomp）。
- **成果物**: docs/MODEL_COMPARISON.md、docs/ROI_EVALUATION_N12_SUMMARY.md、outputs/*.json（gitignore）。rolling validation の summary は model_type / feature_set / n_windows / overall_roi_selected 等の標準キーで統一。

更新日: プロジェクトのマイルストーンごとに更新する。

## Latest Experiment

---
experiment_id: EXP-0006
date: "2026-03-09"
status: completed
objective: 正式 reference（top_n=6, ev=1.05）周辺の局所最適化。top_n=6 固定で ev 再探索・ev=1.05 固定で top_n 近傍探索・bet sizing 比較。ドキュメント整合性回復（暫定/正式の区別、bet sizing 正式表）。
model: xgboost
calibration: sigmoid
features: extended_features
strategy: top_n_ev
parameters:
  best_selection: top_n=6, ev=1.00
  formal_reference_prior: top_n=6, ev=1.05
validation:
  method: rolling_validation
  n_windows: 12
seed: 42
decision: adopt top_n=6, ev=1.00 as 正式 reference 周辺の局所最適（-18.78%, 旧 ev=1.05 の -19.71% より約 0.9pt 改善）
priority: high
tags:
  - exp0006
  - local_opt
  - topn6_ev105
related_experiments:
  - EXP-0005
---

# EXP-0006 正式 reference 周辺の局所最適化

## Purpose

正式 reference（top_n=6, ev=1.05, -19.71% n_w=12）周辺で ev 細かく再探索（1.00, 1.02, 1.05, 1.07, 1.10）と top_n 近傍（5, 6, 7）、最良条件での bet sizing 比較。暫定 best / 正式 reference の区別と bet sizing 正式表でドキュメント整合性を回復。

## Results (n_w=12)

- **Task1** top_n=6 ev sweep: 最良 **ev=1.00 → -18.78%**（1.05:-19.71%）
- **Task2** ev=1.05 top_n sweep: 最良 top_n=6 → -19.71%
- **Task3** bet sizing（top_n=6, ev=1.00）: fixed -18.78%, half_kelly -96.79%, capped_0.02 -23.51%, capped_0.05 -47.70%

## Conclusion

- **adopt** top_n=6, ev=1.00（-18.78%）を正式 reference（top_n=6 系統）の更新として採用。旧 ev=1.05（-19.71%）より約 0.9pt 改善。
- bet sizing は fixed 推奨。leaderboard に正式表を追加済み。

## Notes

- script: scripts/exp0006_local_opt_topn6_ev105.py
- output: outputs/exp0006_local_opt_topn6_ev105.json
- experiment log: experiments/logs/EXP-0006_strategy_grid.md
