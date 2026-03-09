# Experiment: EXP-0010 Race Filter Selection (race_filtered_top_n_ev)

## experiment id

EXP-0010

## purpose

ROI 改善のため、レース単位のフィルタを追加した selection strategy「race_filtered_top_n_ev」を導入し、ベースライン top_n_ev と比較する。レース指標（race_max_ev, race_prob_gap_top1_top2, race_entropy, candidate_count_above_threshold）でフィルタし、通過レースのみ top_n_ev で買い目選定する。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- n_windows: 12, seed: 42
- tool: `python3 -m kyotei_predictor.tools.run_race_filter_experiment`
- output: outputs/race_filter_experiments/exp0010_race_filter_results.json

### ベースライン

- strategy: top_n_ev, top_n: 3, ev_threshold: 1.15 / 1.18 / 1.20

### race_filtered_top_n_ev

- 初期ルール: race_max_ev >= 1.15, race_prob_gap_top1_top2 >= prob_gap_min, race_entropy <= entropy_max, candidate_count_above_threshold >= 1
- 実験パラメータ: top_n = 2,3 / ev_threshold = 1.15, 1.18, 1.20 / prob_gap = 0.03, 0.05, 0.07 / entropy_max = 1.5, 1.7
- 本ログは --quick（1 条件: top_n=3, ev=1.18, pg=0.05, ent=1.7）の結果を含む。

## results

### Quick run（4 strategies, n_w=12）

| strategy_name | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct |
|---------------|---------------------|---------------------|---------------------|
| top_n_ev_ev118 | **-14.54%** | 15,407 | 4.78 |
| top_n_ev_ev120 | -14.88% | 15,249 | 4.72 |
| top_n_ev_ev114 | -15.03% | 15,618 | 4.83 |
| racefilter_top3_ev118_pg5_ent17 | -22.45% | 1,993 | 1.3 |

### ROI ランキング（overall_roi_selected 降順）

1. top_n_ev_ev118: **-14.54%**（ベースライン最良）
2. top_n_ev_ev120: -14.88%
3. top_n_ev_ev114: -15.03%
4. racefilter_top3_ev118_pg5_ent17: -22.45%

## conclusion

- 現行ベースライン（top_n_ev, ev=1.18）が最良（-14.54%）。race_filtered_top_n_ev（pg=0.05, ent=1.7）は bet 数が大きく減少（1,993）するが ROI は悪化（-22.45%）。
- レースフィルタで「不安定レース」を除外すると bet 数は減るが、本設定では ROI 改善には至らなかった。パラメータグリッド全体の実行（--quick なし）で最良組み合わせの探索を推奨。

## notes

- 実行（quick）: `PYTHONPATH=. python3 -m kyotei_predictor.tools.run_race_filter_experiment --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42 --quick`
- フルグリッド: 上記から `--quick` を外す（戦略数 39、所要時間長め）。
- 実装: kyotei_predictor/strategies/race_filtered_top_n_ev.py（race_feature_calculation → race_filter → bet_selection）。
