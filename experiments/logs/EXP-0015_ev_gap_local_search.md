# Experiment: EXP-0015 EV gap 局所探索（top_n_ev_gap_filter）

## experiment id

EXP-0015

## purpose

EXP-0013 の勝ち筋を深掘りする。top_n_ev_gap_filter の局所探索を追加し、ev_gap_threshold と ev_threshold の細かい組み合わせを n_w=12 で検証する。-13.81% を上回る条件があるか確認する。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- strategy: top_n_ev_gap_filter, top_n: 3
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_ev_gap_local_search_experiment`
- output: outputs/ev_gap_experiments/exp0015_ev_gap_local_search_results.json

### ベースライン（EXP-0013 ベスト）

- ev_threshold=1.18, ev_gap_threshold=0.05, overall_roi_selected=-13.81%

### 局所探索グリッド

- ev_threshold: 1.17, 1.18, 1.19, 1.20
- ev_gap_threshold: 0.03, 0.04, 0.05, 0.06, 0.07
- 計 20 条件

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_ev_gap_local_search_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

| strategy_name | ev_threshold | ev_gap_threshold | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|--------------|------------------|---------------------|---------------------|---------------------|-------------------|
| evgap_0x03_top3ev117 | 1.17 | 0.03 | -17.96% | 15,194 | 4.54% | -4.15% |
| evgap_0x04_top3ev117 | 1.17 | 0.04 | -17.56% | 15,120 | 4.54% | -3.75% |
| evgap_0x05_top3ev117 | 1.17 | 0.05 | -16.93% | 15,019 | 4.56% | -3.12% |
| evgap_0x06_top3ev117 | 1.17 | 0.06 | -16.84% | 14,954 | 4.53% | -3.03% |
| evgap_0x07_top3ev117 | 1.17 | 0.07 | -16.67% | 14,879 | 4.50% | -2.86% |
| evgap_0x03_top3ev118 | 1.18 | 0.03 | -14.16% | 15,158 | 4.67% | -0.35% |
| evgap_0x04_top3ev118 | 1.18 | 0.04 | -16.38% | 15,065 | 4.58% | -2.57% |
| evgap_0x05_top3ev118 | 1.18 | 0.05 | -13.81% | 14,994 | 4.63% | 0.0% |
| evgap_0x06_top3ev118 | 1.18 | 0.06 | -16.20% | 14,899 | 4.51% | -2.39% |
| evgap_0x07_top3ev118 | 1.18 | 0.07 | -14.39% | 14,856 | 4.55% | -0.58% |
| evgap_0x03_top3ev119 | 1.19 | 0.03 | -16.90% | 15,052 | 4.55% | -3.09% |
| evgap_0x04_top3ev119 | 1.19 | 0.04 | -16.89% | 14,996 | 4.53% | -3.08% |
| evgap_0x05_top3ev119 | 1.19 | 0.05 | -16.84% | 14,900 | 4.49% | -3.03% |
| evgap_0x06_top3ev119 | 1.19 | 0.06 | -16.75% | 14,835 | 4.46% | -2.94% |
| evgap_0x07_top3ev119 | 1.19 | 0.07 | -15.71% | 14,763 | 4.44% | -1.90% |
| evgap_0x03_top3ev120 | 1.20 | 0.03 | -16.29% | 15,019 | 4.43% | -2.48% |
| evgap_0x04_top3ev120 | 1.20 | 0.04 | -13.15% | 14,936 | 4.45% | +0.66% |
| evgap_0x05_top3ev120 | 1.20 | 0.05 | -13.15% | 14,847 | 4.40% | +0.66% |
| evgap_0x06_top3ev120 | 1.20 | 0.06 | -13.03% | 14,780 | 4.38% | +0.78% |
| evgap_0x07_top3ev120 | 1.20 | 0.07 | **-12.71%** | 14,700 | 4.35% | **+1.10%** |

## baseline comparison

- ベースライン EXP-0013 ベスト: ev=1.18, ev_gap=0.05 → **-13.81%**（n_w=12）
- **ev=1.20, ev_gap=0.07** が最良 **-12.71%**（+1.10%pt）。ベースラインを**上回った**。
- ev=1.20 系統（ev_gap=0.04, 0.05, 0.06, 0.07）はいずれもベースラインを上回る。
- ev=1.17, 1.19 は全条件でベースライン未達。

## conclusion

- **実行完了**: 実験実行済み。結果 JSON: outputs/ev_gap_experiments/exp0015_ev_gap_local_search_results.json。
- **結論**: top_n_ev_gap_filter（ev=1.20, ev_gap_threshold=0.07）を**採用**。overall_roi_selected **-12.71%** で現行ベスト（-13.81%）を 1.10%pt 改善。bet 数は 14,700 で運用可能水準。

## learning

- ev_threshold を 1.18 → 1.20 に上げ、ev_gap を 0.05 → 0.07 に上げることで ROI が改善。より厳格な EV と曖昧レース skip の組み合わせが有効。
- ev=1.17 は閾値が緩く bet 数が増え ROI 悪化。ev=1.19 は局所的に悪い領域の可能性。

## next action

- 採用: top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap_threshold=0.07 を新ベストとして leaderboard に反映。
- ev=1.20 周辺（1.19, 1.21）と ev_gap=0.07 周辺（0.06, 0.08）の追加探索は必要に応じて検討。
