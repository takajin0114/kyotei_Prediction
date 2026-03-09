# Experiment: EXP-0006 Strategy Grid Search

## experiment id

EXP-0006

## purpose

XGBoost + sigmoid + extended_features を固定し、top_n sweep / ev_threshold sweep / bet sizing 比較を行う。ev_threshold_only は不採用。

## configuration

- model: xgboost
- calibration: sigmoid
- features: extended_features
- strategy: top_n_ev
- n_windows: 6
- seed: 42
- output: outputs/exp0006_strategy_grid.json

## Task1: top_n sweep (ev_threshold=1.20 固定)

| top_n | overall_roi_selected | mean_roi | median_roi | std_roi | total_bets | profit | max_drawdown |
|-------|---------------------|----------|------------|---------|------------|--------|--------------|
| 3 | **-10.94%** | -12.09 | -6.75 | 24.61 | 7911 | -86,540 | 111,400 |
| 4 | -27.99% | -27.80 | -27.23 | 10.26 | 19109 | -534,830 | 534,830 |
| 5 | -29.10% | -29.06 | -30.75 | 10.84 | 21781 | -633,830 | 633,830 |
| 6 | -23.71% | -23.48 | -28.59 | 9.14 | 24056 | -570,460 | 570,460 |
| 8 | -27.66% | -27.53 | -26.50 | 8.08 | 27712 | -766,560 | 766,560 |

**最良: top_n=3**（ROI -10.94%）

## Task2: ev_threshold sweep (top_n=6 固定)

| ev_threshold | overall_roi_selected | mean_roi | median_roi | total_bets | profit | max_drawdown |
|--------------|---------------------|----------|------------|------------|--------|--------------|
| 1.05 | -19.38% | -20.18 | -17.29 | 12165 | -235,760 | 235,760 |
| 1.10 | -20.49% | -21.39 | -17.28 | 11812 | -241,980 | 241,980 |
| 1.15 | -20.62% | -21.54 | -17.00 | 11478 | -236,720 | 236,720 |
| 1.20 | -23.71% | -23.48 | -28.59 | 24056 | -570,460 | 570,460 |
| 1.25 | -20.19% | -21.10 | -15.57 | 10857 | -219,180 | 219,180 |

top_n=6 固定では ev=1.05 が最良（-19.38%）。reference の ev=1.20 は -23.71%。

## Task3: bet sizing comparison (最良パラメータ top_n=3, ev=1.20)

| bet_sizing | overall_roi_selected | total_stake | total_payout | profit | max_drawdown | bet_count |
|------------|---------------------|-------------|--------------|--------|--------------|-----------|
| fixed | -10.94% | 791,100 | 704,560 | -86,540 | 161,030 | 7911 |
| half_kelly | -96.69% | 103,426 | 3,426 | -100,000 | 100,000 | 7911 |
| capped_kelly_0.02 | **-8.66%** | 1,154,407 | 1,054,407 | -99,999.76 | 247,197 | 7911 |
| capped_kelly_0.05 | -38.11% | 262,385 | 162,386 | -99,999.90 | 99,999.90 | 7911 |

**最良 bet sizing: capped_kelly_0.02**（ROI -8.66%）。half_kelly / capped_0.05 は資金制約で破綻に近い結果。

## summary

- **最良戦略**: top_n=3, ev_threshold=1.20 → overall_roi_selected **-10.94%**（fixed）
- **最良 bet sizing**: capped_kelly_0.02 で **-8.66%**（同一 bet 列）
- reference（top_n=6, ev=1.20）の -20.7%（n_w=12）より、top_n=3 で約 10pt 改善（n_w=6 時点）
- n_windows=12 での再計測を推奨
