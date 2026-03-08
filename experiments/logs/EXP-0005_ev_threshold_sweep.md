# Experiment: EV Threshold Sweep (ev_threshold_only)

## experiment id

EXP-0005

## strategy

ev_threshold_only（top_n 制限なし、EV >= threshold の全候補を購入）

## parameters

- ev_thresholds: 1.05, 1.10, 1.15, 1.20, 1.25
- model: baseline (sklearn)
- calibration: sigmoid
- n_windows: 6

## results

| ev_threshold | overall_roi | mean_roi | median_roi | bet_count | profit | max_drawdown |
|--------------|-------------|----------|------------|-----------|--------|--------------|
| 1.05 | -48.95% | -49.05 | -50.38 | 212614 | -10,406,510 | 10,406,510 |
| 1.10 | -49.56% | -49.65 | -49.48 | 204223 | -10,121,210 | 10,121,210 |
| 1.15 | -50.83% | -50.95 | -49.52 | 196230 | -9,974,130 | 9,974,130 |
| 1.20 | -51.23% | -51.49 | -51.53 | 188699 | -9,667,800 | 9,667,800 |
| 1.25 | -51.35% | -51.61 | -51.55 | 181616 | -9,325,560 | 9,325,560 |

## analysis

- 低い threshold (1.05) が最良の ROI（-48.95%）。閾値を上げるほど ROI は悪化。
- ev_threshold_only は top_n_ev より購入点数が増えるため、fixed stake では損失が拡大。
- Kelly ベットサイズ導入（kelly_capped）で賭け金を確率・オッズに応じて調整すれば ROI 改善の余地あり。
- n_windows=6 で短めの検証。12 window での再検証を推奨。

## next steps

1. Kelly capped（cap 0.05）で bet_size = bankroll * kelly を検証パイプラインに組み込み
2. n_windows=12 で ev_threshold_sweep を再実行
3. top_n_ev との直接比較（同条件・同閾値）
