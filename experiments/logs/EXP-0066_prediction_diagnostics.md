# EXP-0066: Prediction Diagnostics

## Purpose

モデル予測の品質を分析し、ROI 改善のボトルネックを特定する。

## Setup

- **Predictions**: EXP-0065 と同様の rolling validation（calib_sigmoid）、n_windows = 36
- **Strategy**: top_n_ev_gap_filter（予測ファイルの selected_bets をそのまま使用）

## 分析項目

1. **Calibration curve** … 予測確率と実現頻度の一致度（プロットは matplotlib 利用時のみ出力）
2. **Brier score** … 日別 verify の平均
3. **Log loss** … 日別 verify の平均
4. **EV bucket performance** … EV 帯別 ROI（1.0-1.2, 1.2-1.5, 1.5-2.0, 2.0+）

## How to run

事前に EXP-0065 で n_w=36 の sigmoid 予測を生成しておく。

```bash
python3 -m kyotei_predictor.tools.run_exp0066_prediction_diagnostics --n-windows 36
```

キャリブレーション曲線プロットを出さない場合:

```bash
python3 -m kyotei_predictor.tools.run_exp0066_prediction_diagnostics --n-windows 36 --no-plot
```

## Output

- **JSON**: `outputs/prediction_diagnostics/exp0066_prediction_diagnostics.json`
- **Calibration plot**（matplotlib あり）: `outputs/prediction_diagnostics/exp0066_calibration_curve.png`

## Results (n_windows=36)

| 指標 | 値 |
|------|-----|
| Brier score | 0.955 |
| Log loss | 5.013 |

### EV bucket ROI

| bucket | ROI | bet_count | total_stake |
|--------|-----|-----------|-------------|
| EV_1.0_1.2 | — | 0 | 0 |
| EV_1.2_1.5 | -29.23% | 5,320 | 532,000 |
| EV_1.5_2.0 | -7.77% | 6,229 | 622,900 |
| EV_2.0_plus | -15.93% | 33,987 | 3,398,700 |

- EV 1.0-1.2 は selected_bets に含まれないため 0 件（戦略が高 EV を選ぶため）。
- EV 1.5-2.0 が相対的にマシ（-7.77%）。1.2-1.5 が最も悪い（-29.23%）。

## Notes

- キャリブレーション曲線を描くには `pip install matplotlib` が必要。未導入時は JSON の `calibration_plot_path` は null（今回の実行環境では未導入のためプロット未生成）。
- 予測ソースは `outputs/calibration_comparison/calib_sigmoid/rolling_roi_predictions`。
