# Experiment Template (YAML Standard)

実験ログは **YAML front matter**（機械可読の要約）と **Markdown 本文**（人間向けの解釈・考察）の2部構成とする。AI は front matter を優先して読み、本文で補足する。

---

以下をコピーして新規実験ログの雛形に使う。

```yaml
---
experiment_id: EXP-XXXX
date: YYYY-MM-DD
status: planned
objective: ""
hypothesis: ""
model: ""
calibration: ""
features:
  - ""
strategy: ""
parameters:
  top_n: null
  ev_threshold: null
validation:
  method: rolling_validation
  n_windows: null
metrics:
  overall_roi_selected: null
  mean_roi_selected: null
  median_roi_selected: null
  std_roi_selected: null
  mean_log_loss: null
  mean_brier_score: null
decision: pending
priority: medium
tags:
  - ""
related_experiments:
  - ""
---
```

## Markdown 本文テンプレート

# EXP-XXXX

## Purpose

## Hypothesis

## Configuration

### Model

### Calibration

### Features

### Betting Strategy

### Parameters

### Validation

## Results

## Interpretation

## Risks / Caveats

## Conclusion

## Next Action
