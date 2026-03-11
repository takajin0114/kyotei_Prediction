# Experiment: EXP-0022 venue 別 EV 閾値戦略（top_n_ev_gap_venue_filter）

## experiment id

EXP-0022

## purpose

top_n_ev_gap_filter に会場別 ev_threshold（venue_ev_config）を適用し、ROI が改善するかを検証する。

## background

- 現行ベスト: EXP-0015（top_n=3, ev=1.20, ev_gap=0.07, ROI -12.71%）。
- 会場ごとに予測精度・オッズ分布が異なる可能性があるため、会場別 EV 閾値（例: TODA=1.23, SUMINOE=1.17）で条件を緩厳し、全体 ROI の改善を試みる。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- strategy: top_n_ev_gap_filter（ベースライン）、top_n_ev_gap_venue_filter（会場別 EV）
- top_n: 3, ev_threshold: 1.20（デフォルト）, ev_gap_threshold: 0.07
- venue_ev_config: {"TODA": 1.23, "SUMINOE": 1.17}（config dict で管理）
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_venue_filter_experiment`
- output: outputs/venue_filter_experiments/exp0022_venue_filter_results.json

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_venue_filter_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

| strategy_name | strategy | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|----------|----------------------|---------------------|--------------------|-------------------|
| baseline_evgap_0x07_top3ev120 | top_n_ev_gap_filter | -14.68% | 14,705 | 4.50% | -1.97% |
| venuefilter_ev120_evgap0x07 | top_n_ev_gap_venue_filter | **-14.6%** | 14,702 | 4.51% | -1.89% |

## best candidate

- strategy_name: **venuefilter_ev120_evgap0x07**
- strategy: top_n_ev_gap_venue_filter
- top_n: 3, ev_threshold: 1.20, ev_gap_threshold: 0.07
- venue_ev_config: {"TODA": 1.23, "SUMINOE": 1.17}
- overall_roi_selected: **-14.6%**
- total_selected_bets: 14,702
- hit_rate_rank1_pct: 4.51%

## baseline comparison

- ベースライン EXP-0015 ベスト（n_w=12 公式）: top_n=3, ev=1.20, ev_gap=0.07 → **-12.71%**
- 今回実行の同一条件ベースライン: -14.68%（データ・窓の違いにより EXP-0015 公式値とは乖離あり）。
- venue filter 適用: -14.6% で、今回実行ベースラインより **+0.08%pt 改善**。EXP-0015 公式ベスト -12.71% は今回の run では未達のため、**全体ベスト更新はなし。会場別 EV はわずかにプラス効果**。

## learning

- 会場別 EV 閾値（TODA=1.23, SUMINOE=1.17）を導入すると、同一 run 内のベースラインよりわずかに ROI が良くなった（-14.68% → -14.6%）。
- 今回の run では EXP-0015 公式値 -12.71% には届かず、データ期間・窓の違いの影響が考えられる。
- venue_ev_config は config dict で管理し、今後の会場追加・閾値チューニングが容易な設計とした。

## next step

- 会場別 EV のグリッド拡張（他会場の追加・閾値の微調整）は必要に応じて実施。
- 現行ベストは EXP-0015（top_n_ev_gap_filter, -12.71%）のまま維持。EXP-0022 は「会場別 EV でわずか改善」として記録し、採用は見送り（reject）。
