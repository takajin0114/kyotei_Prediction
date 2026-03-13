# Experiment: EXP-0025 confidence-weighted sizing rollout to ROI-top strategies

## experiment id

EXP-0025

## purpose

confidence-weighted sizing（ev_gap_high=0.11, normal_unit=0.5）を ROI 上位 3 戦略（EXP-0015, EXP-0013, EXP-0007）に横展開し、fixed_base と同一条件 n_windows=12 で比較する。ROI・total_profit・max_drawdown・profit_per_1000_bets・bet_count の総合評価で採用判断する。

## background

- EXP-0024 で ev_gap_high=0.11, normal_unit=0.5 が EXP-0015 条件で最良と確認。
- 他戦略（EXP-0013, EXP-0007）でも weighted が fixed より改善するか検証する。

## baseline

- model: xgboost, calibration: sigmoid, features: extended_features, seed: 42, n_windows: 12
- 戦略: EXP-0015（top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap=0.07）, EXP-0013（同 top_n=3, ev=1.18, ev_gap=0.05）, EXP-0007（top_n_ev, top_n=3, ev=1.18）
- sizing 比較: fixed_base（1.0 unit） vs confidence_weighted（ev_gap_high=0.11, normal_unit=0.5）

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_confidence_weighted_sizing_rollout \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12
```

## results table

| strategy_id | sizing_name        | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|-------------|--------------------|---------|--------------|-------------|----------------------|-----------|
| exp0015     | fixed_base         | -14.68% | -215,840     | 240,390     | -14,678.0            | 14,705    |
| exp0015     | confidence_weighted| **-14.20%** | **-206,545** | **232,595** | **-14,045.9**        | 14,705    |
| exp0013     | fixed_base         | -13.81% | -207,010     | 230,260     | -13,806.19           | 14,994    |
| exp0013     | confidence_weighted| **-13.61%** | **-201,035** | **225,735** | **-13,407.7**        | 14,994    |
| exp0007     | fixed_base         | -14.54% | -224,090     | 243,250     | -14,544.69           | 15,407    |
| exp0007     | confidence_weighted| **-14.00%** | **-209,575** | **232,230** | **-13,602.58**       | 15,407    |

## best candidate

- **同一 run 内 ROI 最良**: exp0013 + confidence_weighted（ROI **-13.61%**）
- **総合**: 3 戦略いずれも confidence_weighted が fixed_base より ROI・total_profit・max_drawdown・profit_per_1000_bets で改善。bet_count は選別が同じため不変。
- **公式 ROI 1 位**: EXP-0015 の -12.71%（別 run）は今回 run では未達。今回 run の exp0015 fixed は -14.68%。

## baseline comparison

- EXP-0015 公式ベスト: ROI -12.71%（n_w=12）。今回 run の fixed は -14.68% のため run 差あり。
- **横展開結論**: EXP-0015 / EXP-0013 / EXP-0007 の 3 戦略すべてで、confidence-weighted（ev_gap_high=0.11, normal_unit=0.5）が fixed より ROI・利益・drawdown・profit_per_1000_bets で一貫して改善。横展開は有効。

## conclusion

- confidence-weighted sizing を 3 戦略に横展開した結果、いずれも fixed より総合指標が改善。
- ROI は公式 1 位（EXP-0015 -12.71%）を今回 run では更新しないが、**hold** として実運用では 3 戦略すべてに confidence-weighted（ev_gap_high=0.11, normal_unit=0.5）の適用を推奨。
- 採用判断: **hold**（ROI adopt は見送り、利益・リスク・効率改善のため実運用候補として推奨）。

## learning

- EV gap のない top_n_ev（EXP-0007）でも、verify 側で ev_gap を combinations から算出するため confidence_weighted_ev_gap_v1 が適用可能。全戦略で同様の改善傾向。
- 横展開により「確信度の高いレースに多く賭ける」 sizing の汎用性が確認できた。

## next action

- 現行ベスト戦略（EXP-0015 fixed）は維持。実運用で confidence-weighted を使う場合は ev_gap_high=0.11, normal_unit=0.5 を全戦略に適用可能。
- 次の実験: max_bets_per_race との組み合わせや venue 別 × weighted は必要時に実施。
