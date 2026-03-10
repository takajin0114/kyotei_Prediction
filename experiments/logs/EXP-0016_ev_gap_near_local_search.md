# Experiment: EXP-0016 EV gap ベスト近傍局所探索（top_n_ev_gap_filter）

## experiment id

EXP-0016

## purpose

EXP-0015 ベスト（ev=1.20, ev_gap=0.07, -12.71%）の近傍を追加探索し、さらに ROI 改善できる条件を探す。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- strategy: top_n_ev_gap_filter, top_n: 3
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_ev_gap_near_local_search_experiment`
- output: outputs/ev_gap_experiments/exp0016_ev_gap_near_local_search_results.json

### ベースライン（EXP-0015 ベスト）

- ev_threshold=1.20, ev_gap_threshold=0.07, overall_roi_selected=-12.71%, selected_bets=14,700

### 追加グリッド

- ev_threshold: 1.19, 1.20, 1.21
- ev_gap_threshold: 0.06, 0.07, 0.08
- 計 9 条件

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_ev_gap_near_local_search_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

| strategy_name | ev_threshold | ev_gap_threshold | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|--------------|------------------|---------------------|---------------------|---------------------|-------------------|
| evgap_0x06_top3ev119 | 1.19 | 0.06 | -16.75% | 14,835 | 4.46% | -4.04% |
| evgap_0x07_top3ev119 | 1.19 | 0.07 | -15.71% | 14,763 | 4.44% | -3.00% |
| evgap_0x08_top3ev119 | 1.19 | 0.08 | -14.55% | 14,683 | 4.50% | -1.84% |
| evgap_0x06_top3ev120 | 1.20 | 0.06 | -13.03% | 14,780 | 4.38% | -0.32% |
| evgap_0x07_top3ev120 | 1.20 | 0.07 | **-12.71%** | 14,700 | 4.35% | 0.0% |
| evgap_0x08_top3ev120 | 1.20 | 0.08 | -14.31% | 14,621 | 4.49% | -1.60% |
| evgap_0x06_top3ev121 | 1.21 | 0.06 | -14.07% | 14,717 | 4.53% | -1.36% |
| evgap_0x07_top3ev121 | 1.21 | 0.07 | -14.35% | 14,640 | 4.50% | -1.64% |
| evgap_0x08_top3ev121 | 1.21 | 0.08 | -13.99% | 14,557 | 4.48% | -1.28% |

## baseline comparison

- ベースライン EXP-0015 ベスト: ev=1.20, ev_gap=0.07 → **-12.71%**（n_w=12）
- 最良は ev=1.20, ev_gap=0.07 のまま（同点）。近傍 9 条件のいずれもベースラインを**上回らなかった**。
- ev=1.19 系統は -14.55%〜-16.75%。ev=1.21 系統は -13.99%〜-14.35%。ev=1.20 & ev_gap=0.06 は -13.03%（-0.32%pt）。

## conclusion

- **実行完了**: 実験実行済み。結果 JSON: outputs/ev_gap_experiments/exp0016_ev_gap_near_local_search_results.json。
- **結論**: EXP-0015 ベスト（ev=1.20, ev_gap=0.07）を**上回る条件はなし**。**採用見送り**。現行ベストは EXP-0015 のまま維持。

## learning

- ev=1.20, ev_gap=0.07 の周辺では局所最適が確認された。ev を 1.19 に下げると ROI 悪化、1.21 に上げても悪化。ev_gap を 0.06 に下げると -13.03%、0.08 に上げると -14.31%。

## next action

- 採用見送り: EXP-0016 では新ベストなし。1 位は EXP-0015（ev=1.20, ev_gap=0.07, -12.71%）のまま。
- 別軸（top_n 変更・他戦略・calibration 等）の検討を検討。
