# Experiment: EXP-0013 EV gap strategy（top_n_ev_gap_filter）

## experiment id

EXP-0013

## purpose

EV gap でレースを skip する戦略により ROI 改善を図る。**ev_gap = ev_rank1 - ev_rank2**（1位と2位の EV 差）。**ev_gap < threshold** ならそのレースを購入対象から外す（skip）。ベースライン top_n_ev (top_n=3, ev=1.18) と比較。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_ev_gap_experiment`
- output: outputs/ev_gap_experiments/exp0013_ev_gap_results.json

### ベースライン

- top_n_ev: top_n=3, ev_threshold=1.18（現行ベスト -14.54%）

### top_n_ev_gap_filter sweep

- ev_gap_threshold: 0.02, 0.03, 0.05, 0.07
- top_n=3, ev_threshold=1.18（ベースラインと同一）

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_ev_gap_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

| strategy_name | ev_gap_threshold | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|------------------|---------------------|---------------------|---------------------|---------------------|
| baseline_top_n_ev | — | -14.54% | 15,407 | 4.78% | 0.0% |
| evgap_0x02_top3ev118 | 0.02 | -14.21% | 15,240 | 4.72% | +0.33% |
| evgap_0x03_top3ev118 | 0.03 | -14.16% | 15,158 | 4.67% | +0.38% |
| evgap_0x05_top3ev118 | 0.05 | **-13.81%** | 14,994 | 4.63% | **+0.73%** |
| evgap_0x07_top3ev118 | 0.07 | -14.39% | 14,856 | 4.55% | +0.15% |

## baseline comparison

- ベースライン top_n_ev top_n=3 ev=1.18: **-14.54%**（n_w=12）
- top_n_ev_gap_filter で **ev_gap_threshold=0.05** が最良 **-13.81%**（+0.73%pt）。ベースラインを**上回った**。
- ev_gap=0.02, 0.03 もベースラインを上回る（+0.33%pt, +0.38%pt）。ev_gap=0.07 は微改善（+0.15%pt）。

## conclusion

- **実行完了**: 実験実行済み。結果 JSON: outputs/ev_gap_experiments/exp0013_ev_gap_results.json。
- **結論**: top_n_ev_gap_filter（ev_gap_threshold=0.05）を**採用**。overall_roi_selected **-13.81%** で現行ベスト（-14.54%）を 0.73%pt 改善。bet 数は 14,994 で運用可能水準。

## learning

- 1位と2位の EV 差が小さいレース（ev_gap < threshold）を skip することで、曖昧なレースを避け ROI が改善した。
- ev_gap_threshold=0.05 が最良。0.07 は skip しすぎて bet 数が減り、逆に ROI がやや悪化。

## next action

- 採用: top_n_ev_gap_filter, top_n=3, ev=1.18, ev_gap_threshold=0.05 を新ベストとして leaderboard に反映。
- 追加 sweep（ev_gap=0.04, 0.06 等）で局所最適の確認を検討。
