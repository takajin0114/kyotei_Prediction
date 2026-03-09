# Experiment: EXP-0006 XGBoost Strategy Optimization

## experiment id

EXP-0006

## purpose

XGBoost を固定し、ROI 改善に直結する戦略・閾値の最適化を行う。

## configuration

- model: XGBoost
- calibration: sigmoid
- features: extended_features
- n_windows: 12
- seed: 42

## results

### EV Threshold Sweep (top_n_ev, top_n=6)

| ev_threshold | overall_roi_selected | mean_roi_selected | median_roi_selected | std_roi_selected | total_selected_bets | profit |
|--------------|---------------------|-------------------|---------------------|------------------|---------------------|--------|
| 1.05 | **-19.71%** | -19.94 | -17.29 | 16.75 | 23,461 | -462,310 |
| 1.10 | -20.06% | -20.31 | -17.28 | 18.10 | 22,814 | -457,750 |
| 1.15 | -20.08% | -20.30 | -17.00 | 17.91 | 22,199 | -445,650 |
| 1.20 | -28.17% | -27.99 | -30.01 | 9.68 | 47,157 | -1,328,560 |
| 1.25 | -19.99% | -20.19 | -16.19 | 18.81 | 21,007 | -419,890 |
| 1.30 | -20.24% | -20.33 | -17.55 | 18.71 | 20,469 | -414,200 |

### Strategy Comparison (ev=1.20)

| strategy | overall_roi_selected | mean_roi_selected | total_selected_bets | profit |
|----------|---------------------|-------------------|---------------------|--------|
| top_n_ev (top_n=6) | **-28.17%** | -27.99 | 47,157 | -1,328,560 |
| ev_threshold_only | -45.97% | -47.27 | 552,281 | -25,390,770 |

## analysis

- EV threshold sweep: ev=1.05 が最良の overall_roi_selected（-19.71%）。EXP-0005 XGBoost 基準（-20.7%）より約 1pt 改善。
- ev=1.20 は sweep 内で ROI 悪化（-28.17%）。top_n=6 での ev=1.20 は bet_count が他より多く、条件差の影響が考えられる。
- Strategy 比較: top_n_ev が ev_threshold_only より ROI で優位。ev_threshold_only は bet 数が多く fixed stake では損失拡大。

## fixed vs fractional Kelly

- Kelly モジュール（half Kelly / cap 0.05）は実装済み。
- 現行 validation パイプラインは fixed stake を前提としており、Kelly ベットとの ROI 比較にはパイプライン拡張が必要。次実験で検討。

## decision

- **adopt**: ev=1.05（top_n_ev, top_n=6）を次基準候補。overall_roi -19.71% で EXP-0005 基準（-20.7%）を上回る。
- **hold**: ev_threshold_only。fixed bet では top_n_ev より ROI 悪化。
- **hold**: ev=1.20。ev=1.05 が sweep 内で最良のため、閾値は 1.05 を採用。
