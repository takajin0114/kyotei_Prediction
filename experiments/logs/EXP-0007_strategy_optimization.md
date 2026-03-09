# Experiment: EXP-0007 Strategy Optimization

## experiment id

EXP-0007

## purpose

Reference（xgboost + sigmoid + extended_features + top_n_ev, top_n=6, ev_threshold=1.05, ROI -19.71%）を基準に、bet sizing 比較・top_n 局所探索・キャリブレーション比較を行う。

## configuration

- model: xgboost
- calibration: sigmoid（Task3 で none / sigmoid / isotonic を比較）
- features: extended_features
- strategy: top_n_ev
- reference: top_n=6, ev_threshold=1.05
- n_windows: 12
- seed: 42
- output: outputs/exp0007_strategy_optimization.json

## Task1: Bet sizing comparison（selection 固定: top_n=6, ev=1.05）

| bet_sizing | overall_roi_selected | profit | max_drawdown | bet_count |
|------------|---------------------|--------|--------------|-----------|
| fixed | -19.71% | -462,310 | 493,400 | 23,461 |
| half_kelly | -96.79% | -100,000 | 100,000 | 23,461 |
| capped_kelly_0.02 | -23.92% | -99,999.75 | 99,999.75 | 23,461 |
| capped_kelly_0.05 | -48.01% | -99,999.91 | 99,999.91 | 23,461 |

**結論**: fixed が最良（-19.71%）。Kelly 系は資金制約で破綻に近い。

## Task2: top_n local search（ev_threshold=1.05 固定）

| top_n | overall_roi_selected | total_selected_bets | profit | max_drawdown |
|-------|---------------------|---------------------|--------|--------------|
| 4 | **-17.85%** | 18,765 | -334,870 | 357,860 |
| 5 | -21.92% | 24,744 | -542,460 | 542,460 |
| 6 | -19.71% | 23,461 | -462,310 | 462,310 |
| 7 | -20.75% | 25,793 | -535,280 | 535,280 |

**結論**: **top_n=4** が最良（-17.85%）。reference の top_n=6（-19.71%）より約 1.9pt 改善。

## Task3: Calibration comparison（同一条件: top_n=6, ev=1.05）

| calibration | overall_roi_selected | total_selected_bets | profit | max_drawdown |
|-------------|---------------------|---------------------|--------|--------------|
| none | **-19.29%** | 52,069 | -1,004,480 | 1,004,480 |
| sigmoid | -19.71% | 23,461 | -462,310 | 462,310 |
| isotonic | -22.13% | 56,879 | -1,258,550 | 1,258,550 |

**結論**: **none** が最良（-19.29%）。sigmoid は -19.71%、isotonic は -22.13%。選択 bet 数は calibration により異なる。

## summary

- **Task1**: bet sizing は fixed を推奨（reference 条件で -19.71%）。
- **Task2**: top_n=4, ev=1.05 で **-17.85%**（reference top_n=6 より改善）。採用検討の余地あり。
- **Task3**: calibration は none がわずかに最良（-19.29%）。sigmoid は -19.71% で従来維持で問題なし。
- 実行: `python3 scripts/exp0007_strategy_optimization.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42`
