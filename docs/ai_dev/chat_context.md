# Chat Context

## Generated At
2026-03-08 11:36:56

## Repository
kyotei_Prediction

## Run Report

<!-- AI開発ワークフロー用ファイル: Cursorがここに実装結果をまとめる -->

# Run Report

## Summary

Generated at: 2026-03-08 11:36:56

## Changed files

```
docs/ai_dev/README.md
docs/ai_dev/run_report.md
scripts/ai_dev_cycle.sh
scripts/generate_run_report.py
```

## Commands run

(実行したコマンドをここに記入)

## Execution results

(実行結果をここに記入)

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

| Rank | Experiment ID | Model | Calibration | Features | Strategy | overall_roi_selected | Notes |
|---|---|---|---|---|---|---|---|
| 1 | EXP-0005 | xgboost | sigmoid | extended_features | top_n_ev | **-20.7%** (n_w=12) | 新 reference 候補 |
| 2 | EXP-0005 | lightgbm | sigmoid | extended_features | top_n_ev | -29.9% (n_w=12) | 安定性良好 |
| 3 | EXP-0004 | sklearn baseline | sigmoid | extended_features | top_n_ev | -27.7% (n_w=12) | 現行 reference |
| 4 | EXP-0001 | sklearn baseline | sigmoid | extended_features | top_n_ev | -28% | 旧 reference |
| - | EXP-0002 | sklearn baseline | sigmoid | extended_features_v2 | top_n_ev | -35% (n_w=2) | v2 比較・hold |
| - | EXP-0004 | sklearn baseline | sigmoid | extended_features_v2 | top_n_ev | -33.76% (n_w=12) | v2 正式比較・hold |

## Notes

- EXP-0005 で sklearn / LightGBM / XGBoost を n_windows=12 で比較。XGBoost が最良 ROI（-20.7%）で adopt。
- この表は主に overall_roi_selected で比較する
- 同程度なら安定性（std_roi_selected）も考慮する
- extended_features_v2 は n_windows=12 でも extended_features より ROI 悪化 → hold
- AI は新しい提案をする前に leaderboard を確認すること

## Project Status

# Project Status

現在のプロジェクト状態。

- **メイン戦略**: Strategy B（baseline B + sigmoid + top_n_ev, top_n=6, ev_threshold=1.20）
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
experiment_id: EXP-0005
date: "2026-03-08"
status: completed
objective: sklearn baseline に対して LightGBM / XGBoost を同条件で比較し、ROI 改善余地を確認する。
model: sklearn baseline / LightGBM / XGBoost
calibration: sigmoid
features: extended_features
strategy: top_n_ev
parameters:
  top_n: 6
  ev_threshold: 1.20
validation:
  method: rolling_validation
  n_windows: 12
seed: 42
decision: adopt XGBoost as next reference
priority: high
tags:
  - model_comparison
  - lightgbm
  - xgboost
related_experiments:
  - EXP-0004
---

# EXP-0005 sklearn / LightGBM / XGBoost モデル比較

## Purpose

sklearn baseline に対して LightGBM / XGBoost を同条件（extended_features, sigmoid, top_n_ev）で rolling validation により比較し、ROI 改善余地を確認する。

## Configuration

- **Models**: sklearn, lightgbm, xgboost
- **Feature set**: extended_features
- **Calibration**: sigmoid
- **Strategy**: top_n_ev（top_n=6, ev_threshold=1.20）
- **Validation**: rolling（n_windows=12）
- **Seed**: 42

## Results (n_windows=12)

| model_type | overall_roi_selected | mean_roi_selected | median_roi_selected | std_roi_selected | total_selected_bets | mean_log_loss | mean_brier_score |
|------------|---------------------|-------------------|---------------------|------------------|---------------------|---------------|------------------|
| sklearn | -31.81 | -31.86 | -33.91 | 12.92 | 46878 | 5.3718 | 0.9376 |
| lightgbm | -29.91 | -29.48 | -30.67 | 11.43 | 26997 | 4.4383 | 0.9464 |
| xgboost | -20.70 | -20.88 | -17.66 | 18.01 | 21581 | 5.0134 | 0.9558 |

## Interpretation

- **XGBoost** が最良の overall_roi_selected（-20.70%）で、sklearn より約 11pt 改善
- LightGBM は sklearn より約 2pt 改善（-29.91%）
- XGBoost は std がやや大きい（18.01）が、ROI の改善幅が大きいため許容
- total_selected_bets は XGBoost が最少（21,581）。EV 閾値でより厳格に絞っている可能性
- LightGBM の log_loss（4.44）が最良

## Conclusion

- **decision**: adopt XGBoost を次基準候補とする
- 次の優先: XGBoost をデフォルトモデルとして運用検討、または LightGBM との追加比較（安定性重視の場合）

## Notes

- latest experiment file: EXP-0005_model_sweep_lightgbm_xgboost.md
- generated by: scripts/generate_chat_context.py
