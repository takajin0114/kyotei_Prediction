# Chat Context

## Generated At
2026-03-09

## Repository
kyotei_Prediction

## Run Report

<!-- AI開発ワークフロー用ファイル: Cursorがここに実装結果をまとめる -->

# Run Report

## Summary

Generated at: 2026-03-09. EXP-0006 n_w=12 正式再評価を実行し、top_n=3, ev=1.20 を new reference として採用（adopt）。

## Changed files

```
experiments/logs/EXP-0006_strategy_grid.md
experiments/leaderboard.md
docs/ai_dev/project_status.md
docs/ai_dev/chat_context.md
```

## Commands run

```bash
python3 scripts/exp0006_recheck_topn3_ev125_n12.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42
```

## Execution results

- Task1 (top_n=3, ev=1.25, n_w=12): overall_roi_selected -15.05%, profit -224,540, max_drawdown 245,110, mean_log_loss 5.013, mean_brier 0.9558
- Task2 (top_n=3 固定 EV sweep): 最良 ev=1.20 → -14.88%（1.22:-15.13%, 1.25:-15.05%, 1.27:-15.63%, 1.30:-15.24%）
- Task3 (bet sizing): fixed -14.88%, half_kelly -96.69%, capped_kelly_0.02 -8.66%, capped_kelly_0.05 -38.11%
- 出力: outputs/exp0006_recheck_n12.json

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

このファイルは主要実験の比較表を管理する。

## ROI Leaderboard

| Rank | Experiment ID | Model | Calibration | Features | Strategy | Parameters | overall_roi_selected | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | EXP-0006 | xgboost | sigmoid | extended_features | top_n_ev | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | **new reference**（正式再評価 adopt） |
| 2 | EXP-0005 | xgboost | sigmoid | extended_features | top_n_ev | top_n=6, ev=1.20 | -20.7% (n_w=12) | 旧 reference |
| 3 | EXP-0005 | lightgbm | sigmoid | extended_features | top_n_ev | - | -29.9% (n_w=12) | 安定性良好 |
| 4 | EXP-0004 | sklearn baseline | sigmoid | extended_features | top_n_ev | - | -27.7% (n_w=12) | sklearn reference |
| 5 | EXP-0001 | sklearn baseline | sigmoid | extended_features | top_n_ev | - | -28% | 旧 reference |
| - | EXP-0002 | sklearn baseline | sigmoid | extended_features_v2 | top_n_ev | - | -35% (n_w=2) | v2 比較・hold |
| - | EXP-0004 | sklearn baseline | sigmoid | extended_features_v2 | top_n_ev | - | -33.76% (n_w=12) | v2 正式比較・hold |

## Notes

- EXP-0006: 暫定ベスト（top_n=3, ev=1.25, n_w=4）を n_w=12 で再評価。ev 微調整の結果 **top_n=3, ev=1.20** が -14.88% で最良 → **new reference adopt**。
- この表は主に overall_roi_selected で比較する。同程度なら安定性（std_roi_selected）も考慮する。
- extended_features_v2 は n_windows=12 でも extended_features より ROI 悪化 → hold。
- AI は新しい提案をする前に leaderboard を確認すること。

## Project Status

# Project Status

現在のプロジェクト状態。

- **メイン戦略**: Strategy B（XGBoost + sigmoid + top_n_ev, **top_n=3, ev_threshold=1.20**）。EXP-0006 n_w=12 正式再評価で new reference adopt（-14.88%）。
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
objective: EXP-0006 暫定ベスト条件（top_n=3, ev=1.25）を n_w=12 で正式再評価し、EV 微調整・bet sizing 比較を行い new reference を決定する。再評価の結果 ev=1.20 が最良のため adopt。
model: xgboost
calibration: sigmoid
features: extended_features
strategy: top_n_ev
parameters:
  top_n: 3
  ev_threshold: 1.20
validation:
  method: rolling_validation
  n_windows: 12
seed: 42
decision: adopt top_n=3, ev=1.20 as new reference（-14.88%）
priority: high
tags:
  - exp0006
  - recheck_n12
  - bet_sizing
related_experiments:
  - EXP-0005
---

# EXP-0006 n_w=12 正式再評価と new reference 採用

## Purpose

暫定ベスト（top_n=3, ev=1.25, n_w=4）を n_windows=12 で再評価し、top_n=3 固定で EV 微調整（1.20, 1.22, 1.25, 1.27, 1.30）と bet sizing 比較を行い、正式な reference を更新する。

## Configuration

- **Model**: xgboost
- **Feature set**: extended_features
- **Calibration**: sigmoid
- **Strategy**: top_n_ev
- **Validation**: rolling（n_windows=12）
- **Seed**: 42

## Results (n_windows=12)

- **Task1** top_n=3, ev=1.25: overall_roi_selected **-15.05%**, profit -224,540, max_drawdown 245,110, mean_log_loss 5.013, mean_brier 0.9558
- **Task2** top_n=3 固定 EV sweep: 最良 **ev=1.20** → **-14.88%**（1.22:-15.13%, 1.25:-15.05%, 1.27:-15.63%, 1.30:-15.24%）
- **Task3** bet sizing（top_n=3, ev=1.20）: fixed -14.88%, half_kelly -96.69%, capped_kelly_0.02 **-8.66%**, capped_kelly_0.05 -38.11%

## Conclusion

- **decision**: **adopt** top_n=3, ev_threshold=1.20 を **new reference** とする（overall_roi_selected -14.88%, 旧 reference -20.7% より約 5.8pt 改善）
- bet sizing は運用上 fixed を推奨（capped_0.02 は ROI 最良だが資金制約で破綻リスクあり）

## Notes

- script: scripts/exp0006_recheck_topn3_ev125_n12.py
- output: outputs/exp0006_recheck_n12.json
- experiment log: experiments/logs/EXP-0006_strategy_grid.md
