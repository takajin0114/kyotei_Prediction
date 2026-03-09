# Experiment: EXP-0011 Prob Pool Selection (top_n_ev_prob_pool)

## experiment id

EXP-0011

## purpose

ROI 改善のため、確率上位Kに限定した候補プール制限型 selection strategy「top_n_ev_prob_pool」を導入し、ベースライン top_n_ev と比較する。pred_prob 上位 pool_k 件のみを候補とし、その中で EV >= ev_threshold の候補から top_n を選ぶ。候補集合を広げすぎず精度を上げる狙い。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_prob_pool_experiment`
- output: outputs/prob_pool_experiments/exp0011_prob_pool_results.json

### ベースライン

- top_n_ev: top_n=3, ev_threshold=1.18 / 1.20

### top_n_ev_prob_pool

- pool_k: 3, 5, 8
- top_n: 2, 3
- ev_threshold: 1.15, 1.18, 1.20
- confidence_type: None（EV のみ。pred_prob / prob_gap は将来拡張可）

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_prob_pool_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

（フルグリッド。`--quick` で 3 戦略のみ。）

## results

結果の詳細は **outputs/prob_pool_experiments/exp0011_prob_pool_results.json** を参照。各 strategy ごとに overall_roi_selected, total_selected_bets, hit_rate_rank1_pct, selected_race_count, selected_race_ratio, avg_bets_per_selected_race, baseline_diff_roi を記録。

### Results table（実行後に JSON から転記）

| strategy_name | overall_roi_selected | baseline_diff_roi | total_selected_bets | selected_race_count | hit_rate_rank1_pct |
|---------------|---------------------|-------------------|---------------------|---------------------|---------------------|
| （exp0011_prob_pool_results.json の results を参照） |

## baseline comparison

- ベースライン top_n_ev ev=1.18: **-14.54%**（n_w=12, leaderboard #1）
- ベースライン top_n_ev ev=1.20: -14.88%
- top_n_ev_prob_pool: 上記 JSON の baseline_diff_roi で比較。

## conclusion

（実行結果に基づき追記。ベースラインを上回った場合は採用判断、上回らなかった場合は採用見送りと学びを記載。）

## learning

- 候補を pred_prob 上位 K に限定することで、ノイズ候補を除き EV 選抜の質を高める設計。pool_k が小さすぎると bet 数が減りすぎ、大きすぎると現行 top_n_ev に近づく。
- rolling_validation_roi の summary に pool_k を記録済み。既存の selected_race_count / selected_race_ratio / avg_bets_per_selected_race で診断可能。

## next action

- ベースラインを上回った場合: 採用し leaderboard 更新。
- 上回らなかった場合: pool_k や confidence_type（pred_prob / prob_gap）の追加 sweep、または別軸の実験へ。
