# Experiment: EXP-0021 top_n × ev × ev_gap 局所探索（top_n_ev_gap_filter）

## experiment id

EXP-0021

## purpose

EXP-0015 周辺の局所探索を **top_n も含めて** 再実施する。現行ベスト -12.71% を上回る条件があるか確認する。

## background

- 現行ベスト: EXP-0015（top_n=3, ev=1.20, ev_gap=0.07, ROI -12.71%）。
- EXP-0016 では ev × ev_gap のみの近傍探索（top_n=3 固定）で同点 -12.71% が最良だった。
- EXP-0020 では max_bets_per_race を直接適用しても差なし。
- 今回は top_n を 2, 3, 4 に広げたグリッドで探索する。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- strategy: top_n_ev_gap_filter
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_ev_gap_topn_local_search_experiment`
- output: outputs/ev_gap_experiments/exp0021_ev_gap_topn_local_search_results.json

## search grid

- top_n: 2, 3, 4
- ev_threshold: 1.19, 1.20, 1.21
- ev_gap_threshold: 0.06, 0.07, 0.08
- 計 3 × 3 × 3 = **27 条件**（EXP-0015 条件 top_n=3, ev=1.20, ev_gap=0.07 を含む）

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_ev_gap_topn_local_search_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

（実験完了後、outputs/ev_gap_experiments/exp0021_ev_gap_topn_local_search_results.json の `results` で表を記載する。）

| strategy_name | top_n | ev_threshold | ev_gap_threshold | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|-------|--------------|------------------|----------------------|---------------------|---------------------|-------------------|
| （JSON で更新） | | | | | | | |

## best candidate

（実験完了後、最良条件を 1 件記載する。）

## baseline comparison

- ベースライン: EXP-0015（top_n=3, ev=1.20, ev_gap=0.07）→ **-12.71%**（n_w=12）, 14,700 bets
- （実験完了後、最良条件の baseline_diff_roi と採用可否を記載する。）

## conclusion

（実験完了後、ベスト更新の有無と採用/見送りを記載する。）

## learning

（実験完了後、top_n を変えた場合の傾向を記載する。）

## next action

（実験完了後に更新する。ベスト更新時は leaderboard / chat_context / project_status を更新。見送り時は Next Experiments を更新。）
