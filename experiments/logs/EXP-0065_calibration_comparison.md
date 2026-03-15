# EXP-0065: Probability Calibration Comparison

## Purpose

Probability calibration の違い（none / sigmoid / isotonic）が ROI・total_profit・max_drawdown 等に与える影響を検証する。

## Setup

- **Strategy**: d_hi475 + switch_dd4000（race_selected_ev フィルタなし）
- **Validation**: rolling validation, n_windows = 36
- **CASE0**: no calibration
- **CASE1**: sigmoid calibration
- **CASE2**: isotonic calibration

## How to run

```bash
python3 -m kyotei_predictor.tools.run_exp0065_calibration_comparison --n-windows 36
```

既存予測のみで再集計する場合（rolling を再実行しない）:

```bash
python3 -m kyotei_predictor.tools.run_exp0065_calibration_comparison --n-windows 36 --skip-rolling
```

## Output

- **JSON**: `outputs/calibration_comparison/exp0065_calibration_results.json`
- **Predictions**: `outputs/calibration_comparison/calib_none/rolling_roi_predictions/`, `calib_sigmoid/`, `calib_isotonic/`

## Results (n_windows=36)

| variant                 | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|-------------------------|---------|--------------|--------------|----------------------|-----------|------------------------|
| CASE0_no_calibration    | -11.71% | -27,982     | 33,992       | -9,427.9             | 2,968     | 6                     |
| CASE1_sigmoid           | **0.53%** | **484**   | 15,886       | **469.45**           | 1,031     | 4                     |
| CASE2_isotonic         | -22.22% | -61,704     | 65,264       | -18,261.02           | 3,379     | 6                     |

- 詳細: `outputs/calibration_comparison/exp0065_calibration_results.json` の `summary` を参照。

## Notes

- EXP-0029 では n_w=12 で sigmoid が isotonic より有利だった。今回は n_w=36 で none / sigmoid / isotonic の 3 条件を比較。
- 各 calibration ごとに別ディレクトリで rolling 予測を生成するため、初回は 3 回分の rolling validation が走り時間がかかる。

## Judgment

**sigmoid 維持（adopt）**。CASE1_sigmoid のみ黒字（ROI 0.53%、total_profit 484、bet_count 1,031）。none は -11.71%、isotonic は -22.22% でいずれも赤字。n_w=36 でも EXP-0029 と同様に sigmoid が最良のため、現行の sigmoid calibration を継続採用する。
