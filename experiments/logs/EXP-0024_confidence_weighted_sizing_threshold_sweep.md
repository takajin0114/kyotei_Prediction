# Experiment: EXP-0024 confidence-weighted sizing threshold sweep

## experiment id

EXP-0024

## purpose

weighted_ev_gap_v1 を基準に ev_gap_high を 0.09 / 0.10 / 0.11 で sweep し、normal_unit を 0.5 / 0.6 / 0.7（ev_gap_high=0.10 時）も比較する。利益効率・drawdown・ROI の総合評価で最適閾値を検証する。

## background

- EXP-0023 で weighted_ev_gap_v1（ev_gap_high=0.10, normal_unit=0.5）が fixed より profit / drawdown / profit_per_1000_bets を改善。
- 閾値微調整でさらに改善余地があるか検証する。

## baseline

- strategy: top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap=0.07
- model: xgboost, calibration: sigmoid, features: extended_features, seed: 42, n_windows: 12
- sizing 比較基準: fixed_base（1.0 unit）

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_confidence_weighted_sizing_threshold_sweep \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12
```

## results table

| sizing_name | ROI | total_profit | max_drawdown | profit_per_1000_bets | bet_count | baseline_diff_roi |
|-------------|-----|--------------|--------------|----------------------|-----------|--------------------|
| fixed_base | -14.68% | -215,840 | 240,390 | -14,678.0 | 14,705 | -1.97% |
| ev_gap_high_0x09_normal0x5 | -14.37% | -210,320 | 235,620 | -14,302.62 | 14,705 | -1.66% |
| ev_gap_high_0x10_normal0x5 | -14.31% | -208,685 | 234,385 | -14,191.43 | 14,705 | -1.60% |
| ev_gap_high_0x11_normal0x5 | **-14.20%** | **-206,545** | **232,595** | **-14,045.90** | 14,705 | **-1.49%** |
| ev_gap_high_0x10_normal0x6 | -14.38% | -210,116 | 235,586 | -14,288.75 | 14,705 | -1.67% |
| ev_gap_high_0x10_normal0x7 | -14.46% | -211,547 | 236,787 | -14,386.06 | 14,705 | -1.75% |

## best candidate

- **sizing_name**: ev_gap_high_0x11_normal0x5
- **config**: ev_gap_high=0.11, normal_unit=0.5（ev_gap>=0.11 → 1.0 unit, それ以外 0.5 unit）
- **ROI**: **-14.20%**（fixed_base -14.68% より +0.48%pt、同一 run 最良）
- **total_profit**: **-206,545**（fixed_base より 9,295 円改善）
- **max_drawdown**: **232,595**（fixed より 7,795 円改善）
- **profit_per_1000_bets**: **-14,045.90**（fixed より bet efficiency 改善）
- **bet_count**: 14,705（選別は同一）

## baseline comparison

- EXP-0015 公式ベスト: ROI -12.71%（n_w=12）。今回 run の fixed_base は -14.68%。
- **ROI**: ev_gap_high_0x11_normal0x5 が fixed_base を **+0.48%pt 上回り**最良。EXP-0015 公式値は未達のため ROI ベスト更新はなし。
- **利益指標**: total_profit・max_drawdown・profit_per_1000_bets はいずれも ev_gap_high_0x11 が fixed および EXP-0023 の 0.10 より改善。

## conclusion

- ev_gap_high を 0.10 → 0.11 に上げると、ROI・利益・drawdown・profit_per_1000_bets がさらに改善した。
- normal_unit は 0.5 が最良で、0.6 / 0.7 は悪化。2 段階の「high=1.0, normal=0.5」を維持するのがよい。
- ROI 観点では EXP-0015 未達のため **adopt は見送り**。利益効率・リスク改善のため **hold** として実運用候補（ev_gap_high=0.11, normal_unit=0.5）を推奨。

## learning

- ev_gap_high のスイープで 0.11 が 0.10 より一貫して良い。より「確信度の高い」レースに多く賭ける方が効率が良い。
- normal_unit を上げると staked が増え、ROI・profit・drawdown はいずれも悪化。0.5 が適切。

## next action

- 現行ベスト戦略は EXP-0015（fixed 1.0 unit）のまま維持。
- confidence-weighted 実運用時は **ev_gap_high=0.11, normal_unit=0.5** を推奨（EXP-0023 の 0.10 より改善）。
- 次の実験: max_bets_per_race との組み合わせ（テーマ B）や venue 別 × weighted sizing（テーマ C）を必要時に実施。
