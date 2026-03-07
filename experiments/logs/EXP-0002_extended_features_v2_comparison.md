---
experiment_id: EXP-0002
date: "2026-03-07"
status: completed
objective: extended_features_v2 を追加し、baseline (sklearn + sigmoid) で extended_features と比較する。
hypothesis: venue_course / recent_form / motor_trend / relative_race_strength 系の追加が ROI 改善に寄与する可能性がある。
model: sklearn baseline
calibration: sigmoid
features:
  - extended_features
  - extended_features_v2
strategy: top_n_ev
parameters:
  top_n: 6
  ev_threshold: 1.20
validation:
  method: rolling_validation
  n_windows: 2
metrics:
  overall_roi_selected: null
  mean_roi_selected: null
  median_roi_selected: null
  std_roi_selected: null
  mean_log_loss: null
  mean_brier_score: null
decision: hold
priority: medium
tags:
  - feature_engineering
  - extended_features_v2
  - baseline
related_experiments:
  - EXP-0001
---

# EXP-0002 extended_features vs extended_features_v2 比較

## Purpose

特徴量セット extended_features_v2（venue_course / recent_form / motor_trend / relative_race_strength 系）を追加し、既存 extended_features と同一条件で rolling validation により比較する。

## Configuration

- **Model**: sklearn baseline
- **Calibration**: sigmoid
- **Strategy**: top_n_ev (top_n=6, ev_threshold=1.20)
- **Validation**: rolling (n_windows=2、本番比較は n_windows=12 推奨)
- **Seed**: 42

## Results (n_windows=2)

| feature_set           | overall_roi_selected | mean_roi_selected | total_selected_bets | mean_log_loss | mean_brier_score |
|----------------------|---------------------|-------------------|----------------------|---------------|------------------|
| current_features     | -20.39%             | -19.72            | 7585                 | 5.230         | 0.948            |
| extended_features    | -17.55%             | -18.23            | 7683                 | 5.253         | 0.946            |
| extended_features_v2 | -35.46%             | -35.12            | 7727                 | 5.317         | 0.945            |

## Interpretation

- 今回の 2 window では extended_features_v2 が extended_features より ROI が悪化している。
- v2 は recent_form を現状 0 のプレースホルダーのみで実装しており、場別・直近成績などの実データが入っていない。
- 次に n_windows=12 で再評価するか、recent_form / venue 成績を DB から組み立ててから再比較することを推奨。

## Conclusion

- **decision**: hold（v2 を基準にはせず、extended_features を維持。v2 は今後の特徴量拡張の土台として利用）
- 次の優先: n_windows=12 での正式比較、または DB 由来の venue/recent 特徴量の追加
