# Experiment: EXP-0029 probability calibration (isotonic)

## experiment id

EXP-0029

## purpose

確率キャリブレーションによる ROI 改善検証。学習時に isotonic regression で model_prob → calibrated_prob とし、EV = calibrated_prob × odds で選別した場合と、現行の sigmoid（baseline）を比較する。

## background

- 現行は CalibratedClassifierCV の sigmoid でキャリブレーション済み。isotonic regression は非線形で確率の順序を保ちつつ補正するため、EV 選別の精度向上が期待される。
- 同一戦略・同一閾値で baseline（sigmoid）vs calibrated（isotonic）の ROI・利益・ドローダウンを比較する。

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_probability_calibration_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --output-dir outputs/probability_calibration_experiments
```

## results table

| strategy_id | condition | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|-------------|-----------|---------|--------------|--------------|----------------------|-----------|
| exp0015     | baseline  | -14.68% | -215,840     | 240,390      | -14,678.0            | 14,705    |
| exp0015     | calibrated | -19.30% | -629,540    | 647,700      | -19,298.61           | 32,621    |
| exp0013     | baseline  | -13.81% | -207,010     | 230,260      | -13,806.19           | 14,994    |
| exp0013     | calibrated | -19.36% | -633,820    | 651,080      | -19,358.6            | 32,741    |
| exp0007     | baseline  | -14.54% | -224,090     | 243,250      | -14,544.69           | 15,407    |
| exp0007     | calibrated | -19.49% | -640,980    | 660,170      | -19,492.75           | 32,883    |

## interpretation

- **ROI**: 全戦略で **baseline（sigmoid）が calibrated（isotonic）を上回る**。isotonic は -19.3%〜-19.5%、sigmoid は -13.8%〜-14.7%。約 5%pt 悪化。
- **bet_count**: isotonic では選別数が約 2 倍（32k 台 vs 15k 台）。calibrated_prob の分布変化により EV 閾値を超える組み合わせが増え、より多くのベットが選択されている。
- **total_profit / max_drawdown**: isotonic は損失・ドローダウンとも大きい。選別数の増加に伴う損失拡大と整合的。
- **結論**: isotonic キャリブレーションは本データ・戦略では ROI を悪化させた。sigmoid を維持する方が有利。

## conclusion

- 確率キャリブレーション（isotonic）は ROI 改善に寄与せず、全戦略で sigmoid baseline より約 5%pt 悪化。
- 採用判断: **reject**（isotonic への切り替えは見送り）。現行の sigmoid キャリブレーションを維持する。

## next action

- 現行ベストは sigmoid のまま。キャリブレーション改善の別案（プラットスケーリング・ベータキャリブレーション等）は必要に応じて検討。
