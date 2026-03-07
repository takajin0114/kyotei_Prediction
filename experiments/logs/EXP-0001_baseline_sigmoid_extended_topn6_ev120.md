---
experiment_id: EXP-0001
date: 2026-03-07
status: completed
objective: "Record the current baseline reference experiment."
hypothesis: "baseline B + sigmoid + extended_features + top_n_ev can serve as the current reference configuration."
model: "sklearn baseline"
calibration: "sigmoid"
features:
  - "extended_features"
strategy: "top_n_ev"
parameters:
  top_n: 6
  ev_threshold: 1.20
validation:
  method: "rolling_validation"
  n_windows: 12
metrics:
  overall_roi_selected: -0.28
  mean_roi_selected: null
  median_roi_selected: null
  std_roi_selected: null
  mean_log_loss: null
  mean_brier_score: null
decision: "adopt"
priority: "high"
tags:
  - "baseline"
  - "reference"
related_experiments: []
---

# EXP-0001

## Purpose

現行ベースライン構成の基準実験を記録する。

## Hypothesis

baseline B + sigmoid + extended_features + top_n_ev の組み合わせが、現時点の基準になる。

## Configuration

### Model

sklearn baseline

### Calibration

sigmoid

### Features

extended_features

### Betting Strategy

top_n_ev

### Parameters

- top_n = 6
- ev_threshold = 1.20

### Validation

- rolling validation
- n_windows = 12

## Results

- overall_roi_selected ≈ -28%
- 戦略パラメータ調整のみでは改善幅は限定的

## Interpretation

EV 閾値や top_n の調整だけでは、ROI を大きく改善できない可能性が高い。

## Conclusion

基準実験として採用。

## Next Action

- model improvement
- feature improvement
- ranking probability decomposition の検討
