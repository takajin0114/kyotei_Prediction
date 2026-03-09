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

Kelly cap: 0.002, 0.005, 0.01, 0.02。同一 selection で bet sizing のみ変更。

| kelly_cap | bet_sizing | overall_roi_selected | profit | max_drawdown | bet_count |
|-----------|------------|---------------------|--------|--------------|-----------|
| (実行後に記載) | capped_kelly_0.002 | - | - | - | - |
| (実行後に記載) | capped_kelly_0.005 | - | - | - | - |
| (実行後に記載) | capped_kelly_0.01 | - | - | - | - |
| (実行後に記載) | capped_kelly_0.02 | - | - | - | - |

**結論**: (実行後に記載)

## Task2: Calibration comparison（none vs sigmoid）

同条件（xgboost, top_n=3, ev=1.20）で ROI 比較。

| calibration | overall_roi_selected | profit | max_drawdown | bet_count |
|-------------|---------------------|--------|--------------|-----------|
| (実行後に記載) | none | - | - | - |
| (実行後に記載) | sigmoid | - | - | - |

**結論**: (実行後に記載)

## Task3: Model / ensemble comparison（EV 計算で比較）

| model | overall_roi_selected | profit | max_drawdown | bet_count |
|-------|---------------------|--------|--------------|-----------|
| (実行後に記載) | xgboost | - | - | - |
| (実行後に記載) | lightgbm | - | - | - |
| (実行後に記載) | ensemble | - | - | - |

**結論**: (実行後に記載)

## summary

- Task1: fractional Kelly の cap を 0.002〜0.02 でスイープ。運用リスクと ROI のトレードオフを確認。
- Task2: calibration none と sigmoid を同条件で比較。
- Task3: xgboost / lightgbm / ensemble（確率平均）の 3 モデルで ROI 比較。

## notes

- 実行: `PYTHONPATH=. python3 scripts/exp0008_fractional_kelly.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42`
- bankroll_simulation で capped_kelly_0.002 / 0.005 / 0.01 / 0.02 をサポート済み。
