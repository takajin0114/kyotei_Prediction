# Experiment: EXP-0030 confidence-weighted sizing 正式比較（EXP-0015 ベースライン）

## experiment id

EXP-0030

## purpose

EXP-0015（top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap=0.07）をベースラインとして、fixed と confidence_weighted sizing（ev_gap_high=0.11, normal_unit=0.5）を正式比較する。EXP-0024・EXP-0025 の知見が EXP-0015 ベスト条件でも再現するか、実運用候補として fixed より優先できるかを検証する。

## background

- EXP-0015 が leaderboard #1（ROI -12.71%, n_w=12）。
- EXP-0023/0024/0025 で confidence_weighted が fixed より total_profit・max_drawdown・profit_per_1000_bets で改善することを確認。ROI は adopt 未達で hold。
- 本実験で EXP-0015 条件に限定し、fixed vs confidence_weighted を同一 run で正式比較する。

## baseline

- model: xgboost, calibration: sigmoid, features: extended_features, seed: 42, n_windows: 12
- 戦略: EXP-0015（top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap=0.07）
- sizing 比較: fixed（1.0 unit） vs confidence_weighted（ev_gap_high=0.11, normal_unit=0.5）

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_exp0030_confidence_weighted_formal_baseline \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12
```

## results table

| sizing_name        | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|--------------------|---------|--------------|--------------|----------------------|-----------|
| fixed              | -14.68% | -215,840     | 240,390      | -14,678.0            | 14,705    |
| confidence_weighted| **-14.20%** | **-206,545** | **232,595** | **-14,045.9**        | 14,705    |

## 指標サマリー

- **ROI**: confidence_weighted が fixed より +0.48%pt 改善（-14.68% → -14.20%）。大きく毀損していない。
- **total_profit**: confidence_weighted が 9,295 円改善（損失幅縮小）。
- **max_drawdown**: confidence_weighted が 7,795 円改善（232,595）。
- **profit_per_1000_bets**: confidence_weighted が 632.1 改善（-14,678 → -14,045.9）。
- **bet_count**: 同一（14,705）。選別条件は同じため不変。

## EXP-0024 / EXP-0025 知見の再現

- EXP-0024（閾値スイープ）・EXP-0025（3戦略横展開）で得られた「ROI を大きく毀損せずに total_profit と max_drawdown が改善する」という知見は、**EXP-0015 ベスト条件でも再現**した。同一 run で fixed より confidence_weighted が全指標で改善。

## 公式ベストとの比較

- EXP-0015 公式ベスト ROI -12.71%（n_w=12）は別 run の数値。今回 run の fixed は -14.68% のため run 差あり。今回 run 内では confidence_weighted が fixed より有利。

## conclusion

- EXP-0015 条件に限定した正式比較で、confidence_weighted が fixed より ROI・total_profit・max_drawdown・profit_per_1000_bets のすべてで改善。
- 実運用候補として **fixed より confidence_weighted を優先できる**（利益・リスク・効率のいずれも改善）。
- ROI のみで見た adopt（公式 -12.71% 更新）は今回 run では未達のため、**採用判断: hold**（実運用では confidence_weighted 推奨）。

## judgment

- **adopt / hold / reject**: **hold**
- 理由: ROI 1 位更新はせず。利益・drawdown・効率の改善が EXP-0015 条件で再現したため、実運用では fixed より confidence_weighted（ev_gap_high=0.11, normal_unit=0.5）を推奨。

## result JSON

outputs/confidence_weighted_sizing_experiments/exp0030_confidence_weighted_formal_baseline_results.json
