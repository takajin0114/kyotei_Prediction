# Experiment: EXP-0026 Kelly sizing experiment

## experiment id

EXP-0026

## purpose

Kelly 型 bet sizing（unit = kelly_fraction * edge / odds, edge = model_prob * odds - 1）を実装し、fixed_base・confidence_weighted と比較する。fraction は 0.25 / 0.5 / 0.75。対象戦略は EXP-0015, EXP-0013, EXP-0007。評価は ROI・total_profit・max_drawdown・profit_per_1000_bets・bet_count。

## background

- EXP-0025 で confidence-weighted が 3 戦略で fixed より改善を確認。
- Kelly は理論上 edge に応じた最適配分だが、モデルが負の edge の場合の挙動と実運用での比較が必要。

## baseline

- model: xgboost, calibration: sigmoid, features: extended_features, seed: 42, n_windows: 12
- 戦略: exp0015, exp0013, exp0007（EXP-0025 と同一）
- sizing 比較: fixed_base, confidence_weighted（ev_gap_high=0.11, normal_unit=0.5）, kelly_0.25, kelly_0.5, kelly_0.75

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_kelly_sizing_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --output-dir outputs/confidence_weighted_sizing_experiments
```

## results table

| strategy_id | sizing_name        | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|-------------|--------------------|---------|--------------|-------------|----------------------|-----------|
| exp0015     | fixed_base         | -14.68% | -215,840     | 240,390     | -14,678.0            | 14,705    |
| exp0015     | confidence_weighted| -14.20% | -206,545     | 232,595     | -14,045.9            | 14,705    |
| exp0015     | kelly_0.25         | -22.97% | -17,298      | 17,298      | -1,176.32            | 14,705    |
| exp0015     | kelly_0.5          | -22.97% | -34,596      | 34,596      | -2,352.65            | 14,705    |
| exp0015     | kelly_0.75         | -22.97% | -51,893      | 51,893      | -3,528.97            | 14,705    |
| exp0013     | fixed_base         | -13.81% | -207,010     | 230,260     | -13,806.19           | 14,994    |
| exp0013     | confidence_weighted| -13.61% | -201,035     | 225,735     | -13,407.7            | 14,994    |
| exp0013     | kelly_0.25         | -22.96% | -17,404      | 17,404      | -1,160.71            | 14,994    |
| exp0013     | kelly_0.5          | -22.96% | -34,807      | 34,807      | -2,321.41            | 14,994    |
| exp0013     | kelly_0.75         | -22.96% | -52,211      | 52,211      | -3,482.12            | 14,994    |
| exp0007     | fixed_base         | -14.54% | -224,090     | 243,250     | -14,544.69           | 15,407    |
| exp0007     | confidence_weighted| -14.00% | -209,575     | 232,230     | -13,602.58           | 15,407    |
| exp0007     | kelly_0.25         | -22.62% | -17,412      | 17,412      | -1,130.14            | 15,407    |
| exp0007     | kelly_0.5          | -22.62% | -34,824      | 34,824      | -2,260.29            | 15,407    |
| exp0007     | kelly_0.75         | -22.62% | -52,236      | 52,236      | -3,390.43            | 15,407    |

## best candidate

- **ROI**: confidence_weighted が全戦略で最良（exp0013 -13.61%）。Kelly は -22.62%〜-22.97% で fixed/confidence_weighted より悪い。
- **total_profit**: Kelly は賭け金が小さくなるため絶対損失は小さい（約 -1.7万〜-5.2 万）。fixed/confidence_weighted は約 -20 万〜-22 万。
- **max_drawdown**: Kelly は大幅に小さい（約 1.7 万〜5.2 万）。fixed/confidence_weighted は約 22 万〜24 万。
- **profit_per_1000_bets**: Kelly は 1 bet あたり損失が小さい（約 -1,130〜-3,528）。fixed/confidence_weighted は約 -13,400〜-14,700。
- **bet_count**: 選別が同じため同一（戦略ごとに 14,705 / 14,994 / 15,407）。

## baseline comparison

- **ROI**: Kelly は fixed・confidence_weighted より約 8〜9%pt 悪い。負の edge で unit が小さくなり賭け金が減るが、回収率は悪化。
- **profit**: Kelly は総損失額は小さい（リスク抑制）。利益最大化ではなく損失・ドローダウン抑制には有効。
- **drawdown**: Kelly は max_drawdown が約 1/10〜1/5 と小さい。
- **efficiency**: profit_per_1000_bets は Kelly の方が「1 bet あたりの損失」は小さいが、ROI は悪化。

## conclusion

- Kelly sizing は **ROI では fixed・confidence_weighted に劣る**。採用（adopt）は見送り。
- **利益・drawdown・efficiency の観点**: 総損失・ドローダウンは Kelly の方が小さい。リスク重視の運用では Kelly は選択肢となりうる。ROI 最適化目的では **reject**。リスク抑制目的では **hold**。

## learning

- モデルが負の edge のレースでも Kelly は unit = max(0, kelly_fraction * edge / odds) で 0 にクランプするため、実質的に賭け金が小さくなる。その結果 total_profit の絶対値・max_drawdown は小さくなるが、ROI は悪化（少額賭けでも負の収支のため）。
- confidence-weighted は ROI・利益・drawdown のバランスで fixed より優位。Kelly は ROI では劣るがリスク指標では有利。

## next action

- 現行推奨は fixed（EXP-0015）または confidence_weighted（実運用推奨）のまま。Kelly は ROI 採用見送り。
- 必要に応じて Kelly の unit_cap や fraction の追加 sweep は可能（本実験では 0.25/0.5/0.75 で一貫して ROI 悪化のため優先度低）。
