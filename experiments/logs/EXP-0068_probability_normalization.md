# EXP-0068: Probability Normalization Experiment

## Purpose

combination probability の正規化により EV 計算の精度を改善する。

## EV 定義

- **baseline**: EV = prob × odds
- **CASE1**: prob_norm = prob / Σ(prob)（レース内 all_combinations の確率和で正規化）、EV = prob_norm × odds

## Setup

- **Selection**: d_hi475（4.30 <= EV < 4.75、prob / prob_norm >= 0.05）
- **Risk control**: switch_dd4000
- **Predictions**: calib_sigmoid, n_windows = 36

## How to run

事前に EXP-0065 で n_w=36 の sigmoid 予測を生成しておく。

```bash
python3 -m kyotei_predictor.tools.run_exp0068_probability_normalization --n-windows 36
```

## Output

- **JSON**: `outputs/probability_normalization/exp0068_probability_normalization.json`

## Results (n_windows=36)

| variant          | ROI   | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|------------------|-------|--------------|--------------|----------------------|-----------|------------------------|
| CASE0_baseline   | -3.5% | -2,932       | 15,266       | -3,109.23            | 943       | 5                     |
| CASE1_prob_norm  | -3.5% | -2,932       | 15,266       | -3,109.23            | 943       | 5                     |

## Notes

- **両 CASE で同一結果**。現在の予測ではレース内の Σ(prob) が既に 1 に近い（モデルがレース単位で正規化済みの可能性）ため、prob_norm ≈ prob となり通過 bet 集合・順序が一致した。
- 正規化の効果を検出するには、レース内で確率和が 1 でないような予測（例: 生スコアのみ）に対して同実験を行う必要がある。
