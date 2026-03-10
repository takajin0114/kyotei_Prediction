# Experiment: EXP-0018 EV gap + odds band filter

## experiment id

EXP-0018

## purpose

EV gap 系（top_n_ev_gap_filter）に **odds band filter** を追加検証する。  
条件: skip if odds_rank1 < odds_low or odds_rank1 > odds_high。1位オッズが帯外のレースを除外し ROI 改善を図る。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- strategy: top_n_ev_gap_filter（ベースライン）、top_n_ev_gap_filter_odds_band（odds band 付き）
- top_n: 3, ev_threshold: 1.20, ev_gap_threshold: 0.07（EXP-0015 ベストと同一）
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_ev_gap_odds_band_experiment`
- output: outputs/ev_gap_experiments/exp0018_ev_gap_odds_band_results.json

### ベースライン

- top_n_ev_gap_filter（odds band なし）: ev=1.20, ev_gap=0.07 → **-12.71%**, selected_bets=14,700

### odds band 候補

- odds_low: 1.2, 1.3, 1.4（skip if odds_rank1 < odds_low）
- odds_high: 20, 25, 30（skip if odds_rank1 > odds_high）

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_ev_gap_odds_band_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

| strategy_name | odds_low | odds_high | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|----------|-----------|---------------------|---------------------|---------------------|-------------------|
| baseline_evgap_top3ev120_evgap0x07 | — | — | **-12.71%** | 14,700 | 4.35% | 0.0% |
| evgap_odds1x2_20 / 1x3_20 / 1x4_20 | 1.2〜1.4 | 20 | -24.94% | 1,867 | 1.29% | -12.23% |
| evgap_odds1x2_25 / 1x3_25 / 1x4_25 | 1.2〜1.4 | 25 | -20.36% | 2,179 | 1.42% | -7.65% |
| evgap_odds1x2_30 / 1x3_30 / 1x4_30 | 1.2〜1.4 | 30 | -22.69% | 2,388 | 1.45% | -9.98% |

（odds_high が同じなら odds_low によらず bet 数・ROI は同一。odds_high=25 が相対的に最良 -20.36%。）

## baseline comparison

- ベースライン（EV gap のみ）: **-12.71%**（n_w=12）, 14,700 bets
- odds band を追加した全条件で **ベースラインを下回った**。最良は odds_high=25 で -20.36%（-7.65%pt）、bets=2,179。bet 数が 1/6 以下に減少し ROI 悪化。

## conclusion

- **実行完了**: 実験実行済み。結果 JSON: outputs/ev_gap_experiments/exp0018_ev_gap_odds_band_results.json。
- **結論**: EV gap + odds band filter は **採用見送り（reject）**。1位オッズ帯でレースを追加 skip すると bet 数が減りすぎ、ROI も悪化。現行ベストは EXP-0015（top_n_ev_gap_filter, ev=1.20, ev_gap=0.07）のまま維持。

## learning

- odds_rank1 を [odds_low, odds_high] に制限すると通過レースが大きく減少（約 2,000 件前後）。その結果、分散が大きくなり ROI が -20%〜-25% に悪化。EV gap のみのフィルタが現時点では最良。

## next action

- 採用見送り: EXP-0018。1 位は EXP-0015 のまま。
- 他軸（別のオッズ指標・閾値の緩い範囲など）は必要に応じて検討。
