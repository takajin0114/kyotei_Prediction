# Experiment: EXP-0023 confidence-weighted fixed sizing

## experiment id

EXP-0023

## purpose

現行ベスト戦略（top_n_ev_gap_filter）はそのままで、fixed sizing のまま confidence（ev_gap / pred_prob_gap）に応じてベットサイズを 2〜3 段階化し、利益指標の改善余地を検証する。ROI 最適化から利益最大化フェーズへの移行を意識した実験とする。

## background

- 現行ベスト: EXP-0015（top_n=3, ev=1.20, ev_gap=0.07, ROI -12.71%）。
- 選別ロジックは変えず、サイズだけ confidence で変えることで、損失削減・drawdown 改善・bet efficiency の向上を図る。

## baseline

- strategy: top_n_ev_gap_filter
- top_n: 3, ev_threshold: 1.20, ev_gap_threshold: 0.07
- model: xgboost, calibration: sigmoid, features: extended_features
- seed: 42, n_windows: 12
- sizing: fixed 1.0 unit（100円/点）

## sizing variants

| 名前 | 内容 | 閾値・単位 |
|------|------|------------|
| fixed_base | 全点 1.0 unit | 100円/点 |
| weighted_ev_gap_v1 | ev_gap で 2 段階 | ev_gap>=0.10 → 1.0, それ以外 0.5 |
| weighted_ev_gap_v2 | ev_gap で 3 段階 | ev_gap>=0.10→1.0, >=0.07→0.75, それ以外 0.5 |
| weighted_prob_gap_v1 | pred_prob_gap で 2 段階 | prob_gap>=0.05→1.0, それ以外 0.5 |

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_confidence_weighted_sizing_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12
```

## results table

| sizing_name | overall_roi_selected | total_selected_bets | total_profit | total_staked | avg_profit_per_window | max_drawdown | profit_per_1000_bets | baseline_diff_roi |
|-------------|----------------------|---------------------|--------------|--------------|------------------------|--------------|----------------------|-------------------|
| fixed_base | -14.68% | 14,705 | -215,840 | 1,470,500 | -17,986.67 | 240,390 | -14,678.0 | -1.97% |
| weighted_ev_gap_v1 | **-14.31%** | 14,705 | **-208,685** | 1,458,450 | **-17,390.42** | **234,385** | **-14,191.43** | **-1.60%** |
| weighted_ev_gap_v2 | -14.49% | 14,705 | -212,262.5 | 1,464,475 | -17,688.54 | 237,387.5 | -14,434.72 | -1.78% |
| weighted_prob_gap_v1 | -17.69% | 14,705 | -165,940 | 937,850 | -13,828.33 | 170,505 | -11,284.6 | -4.98% |

## best candidate

- **sizing_name**: weighted_ev_gap_v1
- **bet_sizing_mode**: confidence_weighted_ev_gap_v1（ev_gap>=0.10 → 1.0 unit, それ以外 0.5 unit）
- **overall_roi_selected**: **-14.31%**（fixed_base -14.68% より +0.37%pt）
- **total_profit**: **-208,685**（fixed_base -215,840 より 7,155 円改善）
- **max_drawdown**: **234,385**（fixed 240,390 より 6,005 円改善）
- **profit_per_1000_bets**: **-14,191.43**（fixed -14,678 より bet efficiency 改善）
- **total_selected_bets**: 14,705（選別は同一）

## baseline comparison

- EXP-0015 公式ベスト: ROI -12.71%（n_w=12）。今回 run の fixed_base は -14.68%（データ・窓の違い）。
- **ROI**: weighted_ev_gap_v1 が fixed_base を **+0.37%pt 上回り**、同一 run 内で最良。EXP-0015 公式値は未達のため ROI ベスト更新はなし。
- **利益指標**: total_profit・max_drawdown・profit_per_1000_bets はいずれも weighted_ev_gap_v1 が fixed より改善。利益最大化観点では **改善あり**。

## conclusion

- confidence-weighted sizing（ev_gap ベース 2 段階）により、**ROI・利益・drawdown・bet efficiency が fixed より改善**した。
- ROI 観点では EXP-0015 未達のため **adopt は見送り**。利益指標改善のため **hold** として実運用候補に据える判断とする。
- weighted_prob_gap_v1 は staked が減り絶対損失は小さいが ROI が悪化（-17.69%）のため採用見送り。

## learning

- ev_gap で high/normal の 2 段階（1.0 / 0.5 unit）が、ROI・profit・drawdown のバランスで最も良かった。
- 3 段階（weighted_ev_gap_v2）は 2 段階よりやや劣る。シンプルな 2 段階を優先するのがよさそう。
- pred_prob_gap ベースは閾値 0.05 では high が少なく staked が減り、ROI は悪化。閾値チューニングは今後の検討課題。

## next action

- 現行ベスト戦略は EXP-0015（fixed 1.0 unit）のまま維持。confidence-weighted（ev_gap v1）は **hold** として利益指標改善オプションに記載。
- 次の実験: 閾値の微調整（ev_gap_high 0.09/0.10/0.11 等）や、他指標との組み合わせを必要時に実施。
