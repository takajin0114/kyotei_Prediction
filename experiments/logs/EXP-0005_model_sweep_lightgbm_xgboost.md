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
