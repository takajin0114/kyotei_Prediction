# Experiment: EXP-0019 EV gap + odds band + max bets per race

## experiment id

EXP-0019

## purpose

EV gap + odds band（top_n_ev_gap_filter_odds_band）に **max bets per race**（1レースあたり最大購入点数）を追加検証する。  
購入点数を 1 または 2 に制限し、ROI 改善を図る。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- strategy: top_n_ev_gap_filter_odds_band（ベースライン）、top_n_ev_gap_filter_odds_band_bet_limit（bet limit 付き）
- top_n: 3, ev_threshold: 1.20, ev_gap_threshold: 0.07, odds_low: 1.3, odds_high: 25
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_ev_gap_odds_band_bet_limit_experiment`
- output: outputs/ev_gap_experiments/exp0019_ev_gap_odds_band_bet_limit_results.json

### ベースライン

- top_n_ev_gap_filter_odds_band（制限なし＝最大3点/レース）: **-20.36%**, selected_bets=2,179

### max_bets_per_race 候補

- 1, 2

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_ev_gap_odds_band_bet_limit_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

| strategy_name | max_bets_per_race | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|-------------------|---------------------|---------------------|---------------------|-------------------|
| baseline_odds1x3_25_top3ev120_evgap0x07 | — | -20.36% | 2,179 | 1.42% | 0.0% |
| odds1x3_25_max1_top3ev120_evgap0x07 | 1 | **-14.25%** | 1,980 | 1.39% | **+6.11%** |
| odds1x3_25_max2_top3ev120_evgap0x07 | 2 | -19.92% | 2,167 | 1.42% | +0.44% |

## baseline comparison

- ベースライン（odds_band のみ、最大3点/レース）: **-20.36%**（n_w=12）, 2,179 bets
- max_bets_per_race=1 で **+6.11%pt 改善**（-14.25%）。max_bets_per_race=2 は +0.44%pt（-19.92%）。
- 現行全体1位は EXP-0015（top_n_ev_gap_filter のみ、-12.71%）。-14.25% はそれには及ばない。

## conclusion

- **実行完了**: 実験実行済み。結果 JSON: outputs/ev_gap_experiments/exp0019_ev_gap_odds_band_bet_limit_results.json。
- **結論**: odds_band 戦略に max_bets_per_race=1 を追加すると ROI が大きく改善（-20.36% → -14.25%）。ただし現行ベスト EXP-0015（-12.71%）を上回ることはなく、**全体1位の採用は見送り**。odds_band を採用する場合は **max_bets_per_race=1 を推奨**する結果となった。

## learning

- 1レースあたりの購入点数を 1 に制限すると、低EVの2・3点目を省き ROI が改善。2 点まで許すとベースラインに近い水準に戻る。

## next action

- 全体1位は EXP-0015（top_n_ev_gap_filter, ev=1.20, ev_gap=0.07）のまま維持。
- odds_band を使う場合は max_bets_per_race=1 を推奨として記録。
- 他軸（top_n_ev_gap_filter のみに max_bets_per_race を適用する等）は必要に応じて検討。
