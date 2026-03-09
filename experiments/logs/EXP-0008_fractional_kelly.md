# Experiment: EXP-0008 Fractional Kelly Optimization

## experiment id

EXP-0008

## purpose

正式 reference（xgboost, sigmoid, extended_features, top_n_ev, top_n=3, ev=1.20, ROI -14.88%）を前提に、(1) fractional Kelly キャップのスイープ、(2) calibration none vs sigmoid の比較、(3) xgboost / lightgbm / ensemble（確率平均）の EV 比較を行う。

## configuration

- reference: model=xgboost, calibration=sigmoid, features=extended_features, strategy=top_n_ev, top_n=3, ev_threshold=1.20
- n_windows: 12
- seed: 42
- script: scripts/exp0008_fractional_kelly.py
- output: outputs/exp0008_fractional_kelly.json

## Task1: Fractional Kelly sweep（selection 固定: top_n=3, ev=1.20）

Kelly cap: 0.002, 0.005, 0.01, 0.02。同一 selection で bet sizing のみ変更。bet_count=15,249。

| kelly_cap | bet_sizing | overall_roi_selected | profit | max_drawdown | bet_count |
|-----------|------------|---------------------|--------|--------------|-----------|
| 0.002 | capped_kelly_0.002 | -14.91% | -99,805 | 167,006 | 15,249 |
| 0.005 | capped_kelly_0.005 | -10.23% | -99,999 | 255,861 | 15,249 |
| 0.01 | capped_kelly_0.01 | **-6.99%** | -99,999 | 356,340 | 15,249 |
| 0.02 | capped_kelly_0.02 | -8.66% | -99,999 | 247,197 | 15,249 |

**結論**: ROI のみ見ると cap=0.01 が最良（-6.99%）。いずれも資金制約で profit が約 -10 万に張り付いており、運用は fixed 推奨。fractional Kelly はリスク抑制効果はあるが破綻リスクは残る。

## Task2: Calibration comparison（none vs sigmoid）

同条件（xgboost, top_n=3, ev=1.20）で ROI 比較。

| calibration | overall_roi_selected | profit | max_drawdown | bet_count |
|-------------|---------------------|--------|--------------|-----------|
| none | -15.80% | -460,470 | 516,540 | 29,150 |
| sigmoid | **-14.88%** | -226,920 | 246,340 | 15,249 |

**結論**: **sigmoid** が有利（-14.88%）。none は -15.80% で bet 数も多い。正式 reference は sigmoid のまま採用。

## Task3: Model / ensemble comparison（EV 計算で比較）

| model | overall_roi_selected | profit | max_drawdown | bet_count |
|-------|---------------------|--------|--------------|-----------|
| xgboost | **-14.88%** | -226,920 | 246,340 | 15,249 |
| lightgbm | -20.90% | -319,010 | 319,010 | 15,262 |
| ensemble | （不具合） | 0 | 0 | 0 |

**結論**: xgboost が lightgbm より約 6pt 良い（-14.88% vs -20.90%）。**ensemble（確率平均）は現状 bet_count=0 で集計されていない不具合あり**。予測マージ時のパス／ファイル参照を要修正。

## summary

- **Task1**: fractional Kelly cap 0.01 で ROI 最良（-6.99%）だが資金制約で破綻に近い。運用は fixed 推奨。
- **Task2**: calibration は sigmoid を採用（-14.88%）。none は -15.80%。
- **Task3**: xgboost > lightgbm。ensemble は不具合のため再実装・再評価が必要。

## notes

- 実行: `PYTHONPATH=. python3 scripts/exp0008_fractional_kelly.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42`
- 結果: outputs/exp0008_fractional_kelly.json（gitignore のためリポジトリには含めない）
- bankroll_simulation で capped_kelly_0.002 / 0.005 / 0.01 / 0.02 をサポート済み。
- **既知の不具合**: Task3 ensemble で xgboost/lightgbm 予測のマージ結果が verify に渡っておらず bet_count=0。要修正。
