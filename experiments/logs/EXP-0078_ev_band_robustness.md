# EXP-0078: EV band robustness test

## 実験目的

EXP-0077 で新主軸候補 **4.50 ≤ EV < 4.90, 0.05 ≤ prob < 0.09**（new_main）が得られた。本実験では n_windows を 24 / 30 / 36 / 48 に拡張し、baseline（旧主軸）と new_main の**頑健性**を比較し、本当に安定した戦略かを確認する。

## 実装内容

- **ツール**: `kyotei_predictor/tools/run_exp0078_ev_band_robustness.py`
- **出力**: `outputs/ev_band_robustness/exp0078_ev_band_robustness.json`（outputs は gitignore のため**未コミット**）
- 既存 calib_sigmoid 予測を利用し、baseline vs new_main を n_windows=24/30/36/48 で評価。

## 共通条件

- calibration: sigmoid
- risk_control: switch_dd4000
- skip_top20pct: true
- **ref_profit**: EXP-0070 と同一（4.30 ≤ EV < 4.75, prob ≥ 0.05）で算出した schedule を各 horizon 内で全 CASE 共通使用

## 比較条件

| variant   | EV 帯            | prob 帯        |
|-----------|------------------|----------------|
| baseline  | 4.30 ≤ EV < 4.75 | 0.05 ≤ prob < 0.09（旧主軸） |
| new_main  | 4.50 ≤ EV < 4.90 | 0.05 ≤ prob < 0.09（新主軸候補） |

## 実験結果（variant × horizon）

| variant   | n_w  | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak | block_profit（要約） |
|-----------|------|--------|--------------|--------------|----------------------|-----------|------------------------|----------------------|
| baseline  | 24   | 145.31%| 13,630       | 3,120        | 133,627.45           | 102       | 11                     | 6 blocks             |
| new_main  | 24   | 211.79%| 15,630       | 2,780        | 192,962.96           | 81        | 6                      | 6 blocks             |
| baseline  | 30   | 84.67% | 10,550       | 5,520        | 75,899.28            | 139       | 12                     | 6 blocks             |
| new_main  | 30   | 143.75%| 13,570       | 4,200        | 128,018.87           | 106       | 12                     | 6 blocks             |
| baseline  | 36   | 62.73% | 8,870        | 7,200        | 55,437.5             | 160       | 12                     | 6 blocks             |
| new_main  | 36   | 159.36%| 17,338       | 5,400        | 139,822.58           | 124       | 12                     | 6 blocks             |
| baseline  | 48   | 59.04% | 10,190       | 7,200        | 51,206.03            | 199       | 12                     | 6 blocks             |
| new_main  | 48   | 155.14%| 19,858       | 5,400        | 134,175.68           | 148       | 12                     | 6 blocks             |

## 採用判断

- **全 horizon（24/30/36/48）で new_main が baseline を上回る**。ROI・total_profit・max_drawdown・profit_per_1000_bets のいずれも new_main が優位。
- **new_main（4.50 ≤ EV < 4.90, 0.05 ≤ prob < 0.09）の頑健性は確認された**。n_w を延ばしても一貫して利益・効率が baseline より良い。
- **n_w=48**: new_main は total_profit 19,858・ROI 155.14%・max_dd 5,400・bet_count 148。長期 horizon でも安定。
- **結論**: 新主軸候補 **new_main** を**実運用主軸として採用（adopt）**。旧主軸 baseline は比較用に維持し、実運用は new_main に更新することを推奨。

## 考察

- EXP-0077 の「ev450_490_prob005_009 が最良」という結果は、n_windows 24/30/36/48 のいずれでも再現した。**EV 帯 4.50–4.90 は horizon に依存せず頑健**。
- max_drawdown は new_main が全 horizon で 2,780〜5,400、baseline は 3,120〜7,200。リスク面でも new_main が有利。
- 次の考察: ref_profit は現状 4.30–4.75 のままなので、主軸を new_main に変更した場合の schedule 整合性や、block 単位モニタリングの継続が妥当。
