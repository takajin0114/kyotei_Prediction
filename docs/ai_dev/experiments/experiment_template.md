# Experiment Template（簡易版）

**推奨**: 新規実験ログは [experiment_template_yaml.md](experiment_template_yaml.md)（YAML standard）を使うこと。こちらは YAML front matter を使わない簡易版。機械可読性が必要な場合は YAML standard を利用する。

## Experiment ID

EXP-XXXX

## Date

YYYY-MM-DD

## Purpose

この実験の目的を書く

## Hypothesis

何を改善すると ROI が改善すると考えたか

## Configuration

### Model

例

- sklearn baseline
- LightGBM
- XGBoost

### Calibration

例

- none
- sigmoid
- isotonic

### Features

例

- current_features
- extended_features
- venue_course_features
- recent_form_features

### Betting Strategy

例

- top_n_ev

### Parameters

例

- top_n = 6
- ev_threshold = 1.20

### Validation

例

- rolling validation
- n_windows = 12

## Metrics

- mean_roi_selected
- median_roi_selected
- std_roi_selected
- overall_roi_selected
- mean_log_loss
- mean_brier_score

## Results

数値を記録する

## Interpretation

結果の解釈を書く

## Conclusion

採用 / 保留 / 却下 を書く

## Next Action

次にやることを書く
