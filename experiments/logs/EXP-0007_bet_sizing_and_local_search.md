# Experiment: EXP-0007 Bet Sizing and Local Search (top_n=3)

## experiment id

EXP-0007

## purpose

正式 reference（top_n=3, ev=1.20, -14.88% n_w=12）の近傍最適化と、bet sizing の正式比較。top_n=3 固定で EV threshold を高解像度探索し、最良条件で bet sizing を比較する。

## configuration

- model: xgboost
- calibration: sigmoid
- features: extended_features
- strategy: top_n_ev
- top_n: 3（固定）
- validation: rolling, n_windows=12, seed=42
- script: scripts/exp0007_local_search_topn3_ev_and_bet_sizing.py
- output: outputs/exp0007_local_search_topn3_ev_and_bet_sizing.json

## Task1: top_n=3 固定で EV threshold 高解像度探索

| ev_threshold | overall_roi_selected | mean_roi_selected | median_roi_selected | std_roi_selected | total_selected_bets | profit | max_drawdown |
|--------------|----------------------|------------------|---------------------|------------------|---------------------|--------|--------------|
| 1.18 | **-14.54%** | -15.0 | -18.23 | 19.5 | 15,407 | -224,090 | 243,250 |
| 1.20 | -14.88% | -15.36 | -17.55 | 20.56 | 15,249 | -226,920 | 246,340 |
| 1.22 | -15.13% | -15.65 | -17.07 | 20.69 | 15,121 | -228,770 | 248,690 |
| 1.24 | -15.24% | -15.76 | -17.12 | 21.17 | 14,992 | -228,520 | 249,340 |
| 1.25 | -15.05% | -15.58 | -16.77 | 21.4 | 14,920 | -224,540 | 245,110 |

**結論**: **ev=1.18** が最良（-14.54%）。正式 reference ev=1.20（-14.88%）より約 0.34pt 改善。ev を上げると ROI は悪化し 1.24 で最悪、1.25 でやや回復。

## Task2: Bet sizing 正式比較（selection: top_n=3, ev=1.18 = Task1 最良）

| bet_sizing | overall_roi_selected | profit | max_drawdown | total_selected_bets |
|------------|---------------------|--------|--------------|---------------------|
| fixed | -14.54% | -224,090 | 279,680 | 15,407 |
| half_kelly | -96.69% | -100,000 | 100,000 | 15,407 |
| capped_kelly_0.02 | **-8.17%** | -99,999.75 | 274,447 | 15,407 |
| capped_kelly_0.05 | -38.17% | -99,999.91 | 99,999.90 | 15,407 |

**結論**: ROI のみ見ると capped_kelly_0.02 が最良（-8.17%）だが、資金制約で破綻に近い（profit -100k、max_dd 大）。運用は **fixed** 推奨。

## Summary

- **Task1**: top_n=3 で ev=1.18 が最良（-14.54%）。正式 reference ev=1.20（-14.88%）より小幅改善 → **adopt** ev=1.18 を reference 更新候補とするか **hold**（差は 0.34pt のみ）。
- **Task2**: bet sizing は fixed 推奨。capped_kelly_0.02 は ROI は良いがリスク大。
- 正式 reference は引き続き top_n=3, ev=1.20 を維持し、ev=1.18 は「局所最適」として記録。
