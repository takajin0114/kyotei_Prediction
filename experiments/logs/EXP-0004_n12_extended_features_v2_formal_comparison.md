---
experiment_id: EXP-0004
date: "2026-03-08"
status: completed
objective: n_windows=12 で extended_features と extended_features_v2 を正式比較し adopt/hold を判断する。
hypothesis: DB 由来の recent_form / venue_course を実装した v2 が extended_features より ROI 改善する可能性がある。
model: sklearn baseline (Strategy B)
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
  n_windows: 12
seed: 42
metrics:
  extended_features: { overall_roi: -27.7, mean_roi: -27.75, total_bets: 47255 }
  extended_features_v2: { overall_roi: -33.76, mean_roi: -33.64, total_bets: 46898 }
decision: hold
priority: high
tags:
  - feature_engineering
  - extended_features_v2
  - n12_formal_comparison
related_experiments:
  - EXP-0001
  - EXP-0002
  - EXP-0003
---

# EXP-0004 n_windows=12 extended_features vs extended_features_v2 正式比較

## Purpose

extended_features_v2（DB 由来 recent_form / venue_course + motor_trend / relative_race_strength）を extended_features と同一条件で rolling validation（n_windows=12）により比較し、adopt/hold を判断する。

## Configuration

- **Model**: sklearn baseline (Strategy B)
- **Calibration**: sigmoid
- **Strategy**: top_n_ev（top_n=6, ev_threshold=1.20）
- **Validation**: rolling（n_windows=12）
- **Seed**: 42

## Results (n_windows=12)

| feature_set | overall_roi_selected | mean_roi_selected | median_roi_selected | std_roi_selected | total_selected_bets | mean_log_loss | mean_brier_score |
|-------------|---------------------|-------------------|---------------------|------------------|---------------------|---------------|------------------|
| extended_features | -27.7 | -27.75 | -30.02 | 10.21 | 47255 | 5.37556 | 0.936333 |
| extended_features_v2 | -33.76 | -33.64 | -32.53 | 12.75 | 46898 | 5.38516 | 0.935519 |

## Interpretation

- extended_features が extended_features_v2 より overall_roi_selected が良好（-27.7% vs -33.76%）
- v2 は recent_form / venue_course を DB 由来で実装済みだが、n12 では ROI が悪化
- mean/std_roi_selected も extended_features の方が安定（std: 10.21 vs 12.75）
- log_loss / Brier は v2 がわずかに悪い（補助指標として v2 の確率キャリブレーションは改善余地あり）

## Conclusion

- **decision**: hold（v2 を基準にはせず extended_features を維持）
- 次の優先: 特徴量の見直し（venue/recent の正規化・重みなど）、または LightGBM/XGBoost sweep
