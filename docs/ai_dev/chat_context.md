# Chat Context

## Generated At
2026-03-09

## Repository
kyotei_Prediction

## Run Report

<!-- AI開発ワークフロー用ファイル: Cursorがここに実装結果をまとめる -->

# Run Report

## Summary

Generated at: 2026-03-09. **EXP-0007** 正式 reference（top_n=3, ev=1.20）近傍の EV 高解像度探索と bet sizing 正式比較を実施。top_n=3 固定で ev [1.18, 1.20, 1.22, 1.24, 1.25] を比較した結果 **ev=1.18 が最良**（-14.54%）→ adopt。旧 reference ev=1.20（-14.88%）より約 0.34pt 改善。bet sizing は fixed 推奨（capped_kelly_0.02 は ROI は良いが資金制約で破綻リスク）。chat_context / leaderboard / project_status を EXP-0007 ベースに同期済み。

## Changed files

```
scripts/exp0007_local_search_topn3_ev_and_bet_sizing.py
experiments/logs/EXP-0007_bet_sizing_and_local_search.md
experiments/leaderboard.md
docs/ai_dev/project_status.md
docs/ai_dev/chat_context.md
```

## Commands run

```bash
PYTHONPATH=. python3 scripts/exp0007_local_search_topn3_ev_and_bet_sizing.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42
```

## Execution results

- Task1 (top_n=3 固定 ev sweep [1.18, 1.20, 1.22, 1.24, 1.25]): 最良 **ev=1.18 → -14.54%**（1.20:-14.88%, 1.24:-15.24%）
- Task2 (bet sizing, 最良条件 top_n=3 ev=1.18): fixed -14.54%, half_kelly -96.69%, capped_kelly_0.02 -8.17%, capped_kelly_0.05 -38.17%
- 出力: outputs/exp0007_local_search_topn3_ev_and_bet_sizing.json

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

## EXP-0007 報告（Task4）

1. **変更ファイル一覧**: scripts/exp0007_local_search_topn3_ev_and_bet_sizing.py（新規）, experiments/logs/EXP-0007_bet_sizing_and_local_search.md（新規）, experiments/leaderboard.md, docs/ai_dev/project_status.md, docs/ai_dev/chat_context.md
2. **実行コマンド**: `PYTHONPATH=. python3 scripts/exp0007_local_search_topn3_ev_and_bet_sizing.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42`
3. **実験結果サマリー**: Task1 最良 ev=1.18（-14.54%）。Task2 bet sizing 最良 ROI は capped_kelly_0.02（-8.17%）だが運用は fixed 推奨。
4. **旧 reference との ROI 比較**: 旧 top_n=3, ev=1.20 → -14.88%。新 top_n=3, ev=1.18 → -14.54%。改善 +0.34pt。
5. **採用判断**: **adopt** top_n=3, ev=1.18 を 1 位として採用。正式 reference は ev=1.20 起点のまま記載を維持。

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
| 1 | EXP-0007 | top_n=3, ev=1.18 | **-14.54%** (n_w=12) | EV 高解像度探索で最良（adopt） |
| 2 | EXP-0006 | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | 正式 reference（従来 1 位） |
| 3 | EXP-0007 | top_n=4, ev=1.05 | -17.85% (n_w=12) | top_n 局所探索（hold） |
| 4 | EXP-0006 | top_n=6, ev=1.00 | -18.78% (n_w=12) | 局所最適（adopt） |
| 5 | EXP-0006 | top_n=6, ev=1.05 | -19.71% (n_w=12) | top_n=6 系統・前回 |
| 6 | EXP-0005 | top_n=6, ev=1.20 | -20.7% (n_w=12) | 旧 reference |

Bet sizing 正式表は experiments/leaderboard.md の「Bet Sizing 比較」を参照（top_n=3 ev=1.18 / ev=1.20 の両条件を記載）。

## Notes

- EXP-0007: 1位 top_n=3, ev=1.18（-14.54%, adopt）。正式 reference は top_n=3, ev=1.20（-14.88%）起点。bet sizing は fixed 推奨。
- AI は新しい提案をする前に leaderboard を確認すること。

## Project Status

# Project Status

現在のプロジェクト状態。

- **メイン戦略**: Strategy B（XGBoost + sigmoid + top_n_ev）。**正式 reference (n_w=12)**: (1) 1位 **top_n=3, ev=1.18**（-14.54%, EXP-0007 adopt）。(2) 2位 **top_n=3, ev=1.20**（-14.88%, 従来正式 reference）。(3) **top_n=6, ev=1.00**（-18.78%, adopt）。暫定 best（n_w=4）の top_n=3, ev=1.25 は未確定。
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
experiment_id: EXP-0007
date: "2026-03-09"
status: completed
objective: 正式 reference（top_n=3, ev=1.20）近傍の EV 高解像度探索（1.18, 1.20, 1.22, 1.24, 1.25）と bet sizing 正式比較。
model: xgboost
calibration: sigmoid
features: extended_features
strategy: top_n_ev
parameters:
  best_selection: top_n=3, ev=1.18
  formal_reference_prior: top_n=3, ev=1.20
validation:
  method: rolling_validation
  n_windows: 12
seed: 42
decision: adopt top_n=3, ev=1.18（-14.54%）。旧 reference ev=1.20（-14.88%）より約 0.34pt 改善。bet sizing は fixed 推奨。
priority: high
tags:
  - exp0007
  - local_search
  - topn3_ev
  - bet_sizing
related_experiments:
  - EXP-0006
---

# EXP-0007 Bet Sizing and Local Search (top_n=3)

## Purpose

正式 reference（top_n=3, ev=1.20, -14.88% n_w=12）の近傍で EV を高解像度探索し、最良条件で bet sizing を正式比較。

## Results (n_w=12)

- **Task1** top_n=3 ev sweep [1.18, 1.20, 1.22, 1.24, 1.25]: 最良 **ev=1.18 → -14.54%**
- **Task2** bet sizing（top_n=3, ev=1.18）: fixed -14.54%, half_kelly -96.69%, capped_kelly_0.02 -8.17%, capped_kelly_0.05 -38.17%

## Conclusion

- **adopt** top_n=3, ev=1.18（-14.54%）を 1 位として採用。ev=1.20 は正式 reference として維持。
- bet sizing は fixed 推奨。leaderboard に top_n=3 ev=1.18 / ev=1.20 の両条件で正式表を記載済み。

## Notes

- script: scripts/exp0007_local_search_topn3_ev_and_bet_sizing.py
- output: outputs/exp0007_local_search_topn3_ev_and_bet_sizing.json
- experiment log: experiments/logs/EXP-0007_bet_sizing_and_local_search.md
