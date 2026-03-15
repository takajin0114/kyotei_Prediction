# EXP-0069: EV Percentile Strategy

## Purpose

EV 固定閾値ではなく、レース内 EV ランキングによる selection を検証する。

## Setup

- **CASE0**: baseline d_hi475（4.30 <= EV < 4.75, prob >= 0.05）
- **CASE1**: レース内 EV 降順で上位 0.5%
- **CASE2**: 上位 1%
- **CASE3**: 上位 2%
- **CASE4**: 上位 5%
- **Risk control**: switch_dd4000
- **Predictions**: calib_sigmoid, n_windows = 36

## How to run

事前に EXP-0065 で n_w=36 の sigmoid 予測を生成しておく。

```bash
python3 -m kyotei_predictor.tools.run_exp0069_ev_percentile --n-windows 36
```

## Output

- **JSON**: `outputs/ev_percentile/exp0069_ev_percentile.json`

## Results (n_windows=36)

| variant                 | ROI    | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|-------------------------|--------|--------------|--------------|----------------------|-----------|------------------------|
| CASE0_baseline_d_hi475  | -3.5%  | -2,932       | 15,266       | -3,109.23            | 943       | 5                     |
| CASE1_top_0_5pct_ev     | -14.31% | -301,932    | 316,472      | -11,525.0            | 26,198    | 6                     |
| CASE2_top_1pct_ev       | -14.31% | -301,932    | 316,472      | -11,525.0            | 26,198    | 6                     |
| CASE3_top_2pct_ev       | -14.31% | -301,932    | 316,472      | -11,525.0            | 26,198    | 6                     |
| CASE4_top_5pct_ev       | -14.31% | -301,932    | 316,472      | -11,525.0            | 26,198    | 6                     |

## Notes

- **baseline（d_hi475）が優位**。ROI -3.5%、bet 943。EV percentile（top 0.5〜5%）は bet が約 26,198 と増え、ROI -14.31%・max_drawdown も悪化。
- CASE1〜4 が同一なのは、レースあたりの selected_bets 数が少ないため、上位 0.5%・1%・2%・5% のいずれも実質同じ本数（例: 1 本）になるレースが多く、結果として採用 bet 集合が一致したため。
- **結論**: 固定閾値 d_hi475 を維持。EV ランキングのみの selection は採用しない（reject）。
