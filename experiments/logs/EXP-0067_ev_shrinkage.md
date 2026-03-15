# EXP-0067: EV Shrinkage Experiment

## Purpose

EV 過大評価を抑えるため、EV_adj = EV^alpha で shrinkage をかけ、selection に EV_adj を使用した場合の効果を検証する。

## EV 定義

- **baseline**: EV = prob × odds
- **CASE1〜4**: EV_adj = EV^alpha（alpha = 0.5, 0.7, 0.8, 0.9）

## Setup

- **Selection**: d_hi475 を EV_adj で適用（4.30^alpha <= EV_adj < 4.75^alpha, prob>=0.05）
- **Risk control**: switch_dd4000
- **Predictions**: calib_sigmoid, n_windows = 36

## How to run

事前に EXP-0065 で n_w=36 の sigmoid 予測を生成しておく。

```bash
python3 -m kyotei_predictor.tools.run_exp0067_ev_shrinkage --n-windows 36
```

## Output

- **JSON**: `outputs/ev_shrinkage/exp0067_ev_shrinkage.json`

## Results (n_windows=36)

| variant             | ROI   | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|---------------------|-------|--------------|--------------|----------------------|-----------|------------------------|
| CASE0_baseline      | -3.5% | -2,932       | 15,266       | -3,109.23            | 943       | 5                     |
| CASE1_ev_power_0_5  | -3.5% | -2,932       | 15,266       | -3,109.23            | 943       | 5                     |
| CASE2_ev_power_0_7  | -3.5% | -2,932       | 15,266       | -3,109.23            | 943       | 5                     |
| CASE3_ev_power_0_8  | -3.5% | -2,932       | 15,266       | -3,109.23            | 943       | 5                     |
| CASE4_ev_power_0_9  | -3.5% | -2,932       | 15,266       | -3,109.23            | 943       | 5                     |

## Notes

- **全 CASE で同一結果**。d_hi475 の EV 帯（4.30〜4.75）が狭く、EV^alpha で変換しても「4.30^alpha <= EV_adj < 4.75^alpha」を通過する bet 集合が baseline と一致し、レース順序（max_ev_adj でソート）も実質同じだった。
- 差を出すには、EV 帯を広げるか、EV_adj 用に別の閾値（例: 一定の EV_adj 帯）を設ける必要がある。
