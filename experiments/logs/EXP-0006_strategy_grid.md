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

- **最良戦略**: top_n=3, ev_threshold=1.20 → overall_roi_selected **-10.94%**（fixed, n_w=6）
- **最良 bet sizing**: capped_kelly_0.02 で **-8.66%**（同一 bet 列）
- reference（top_n=6, ev=1.20）の -20.7%（n_w=12）より、top_n=3 で約 10pt 改善（n_w=6 時点）
- n_windows=12 での再計測を推奨

---

## 正式再評価 (n_windows=12, exp0006_recheck_topn3_ev125_n12.py)

### Task1: top_n=3, ev_threshold=1.25 単体 (n_w=12)

| 指標 | 値 |
|------|-----|
| overall_roi_selected | -15.05% |
| mean_roi_selected | -15.58 |
| median_roi_selected | -16.77 |
| std_roi_selected | 21.40 |
| total_selected_bets | 14,920 |
| profit | -224,540 |
| max_drawdown | 245,110 |
| mean_log_loss | 5.013374 |
| mean_brier_score | 0.95577 |

### Task2: top_n=3 固定 EV threshold 微調整 (n_w=12)

| ev_threshold | overall_roi_selected | mean_roi | total_bets | profit | max_drawdown |
|--------------|---------------------|----------|------------|--------|--------------|
| 1.20 | **-14.88%** | -15.36 | 15,249 | -226,920 | 246,340 |
| 1.22 | -15.13% | -15.65 | 15,121 | -228,770 | 248,690 |
| 1.25 | -15.05% | -15.58 | 14,920 | -224,540 | 245,110 |
| 1.27 | -15.63% | -16.15 | 14,795 | -231,190 | 250,950 |
| 1.30 | -15.24% | -15.73 | 14,614 | -222,780 | 242,750 |

**最良: top_n=3, ev_threshold=1.20**（n_w=12 で -14.88%）

### Task3: bet sizing 比較 (最良条件 top_n=3, ev=1.20, n_w=12)

| bet_sizing | overall_roi_selected | profit | max_drawdown | total_selected_bets |
|------------|---------------------|--------|--------------|---------------------|
| fixed | -14.88% | -226,920 | 283,570 | 15,249 |
| half_kelly | -96.69% | -100,000 | 100,000 | 15,249 |
| capped_kelly_0.02 | **-8.66%** | -99,999.76 | 247,197 | 15,249 |
| capped_kelly_0.05 | -38.11% | -99,999.90 | 99,999.90 | 15,249 |

### 正式結果サマリ

- **n_w=12 最良 selection**: top_n=3, ev_threshold=1.20 → **-14.88%**（旧 reference -20.7% より約 5.8pt 改善）
- **new reference 採用**: top_n=3, ev=1.20（adopt）。暫定ベストだった top_n=3, ev=1.25 は n_w=12 で -15.05% のため、ev=1.20 を正式採用。
- bet sizing は fixed を基準とし、capped_kelly_0.02 が ROI 最良（資金制約で破綻リスクありのため fixed を運用基準とする場合あり）
- 再評価実行: `python3 scripts/exp0006_recheck_topn3_ev125_n12.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42` → outputs/exp0006_recheck_n12.json

---

## 局所最適化（正式 reference 周辺, n_w=12, exp0006_local_opt_topn6_ev105.py）

正式 reference（top_n=6, ev=1.05, -19.71%）周辺で ev 細かく再探索と top_n 近傍探索を実施。

### Task1: top_n=6 固定 ev_threshold 再探索 (n_w=12)

| ev_threshold | overall_roi_selected | mean_roi_selected | median_roi_selected | std_roi_selected | total_selected_bets | profit | max_drawdown |
|--------------|---------------------|-------------------|---------------------|------------------|---------------------|--------|--------------|
| 1.00 | **-18.78%** | -18.98 | -15.66 | 15.52 | 24,172 | -453,890 | 453,890 |
| 1.02 | -19.17% | -19.35 | -15.54 | 15.99 | 23,902 | -458,130 | 458,130 |
| 1.05 | -19.71% | -19.94 | -17.29 | 16.75 | 23,461 | -462,310 | 462,310 |
| 1.07 | -19.63% | -19.85 | -17.58 | 17.20 | 23,193 | -455,290 | 455,290 |
| 1.10 | -20.06% | -20.31 | -17.28 | 18.10 | 22,814 | -457,750 | 457,750 |

**最良: ev=1.00**（-18.78%。正式 reference ev=1.05 の -19.71% より約 0.9pt 改善）

### Task2: ev=1.05 固定 top_n 近傍 (n_w=12)

| top_n | overall_roi_selected | mean_roi_selected | median_roi_selected | std_roi_selected | total_selected_bets | profit | max_drawdown |
|-------|---------------------|-------------------|---------------------|------------------|---------------------|--------|--------------|
| 5 | -21.92% | -21.11 | -23.86 | 15.80 | 24,744 | -542,460 | 542,460 |
| 6 | **-19.71%** | -19.94 | -17.29 | 16.75 | 23,461 | -462,310 | 462,310 |
| 7 | -20.75% | -20.79 | -18.21 | 12.14 | 25,793 | -535,280 | 535,280 |

**最良: top_n=6**（ev=1.05 固定時）

### Task3: bet sizing 比較（最良 selection: top_n=6, ev=1.00, n_w=12）

| bet_sizing | overall_roi_selected | profit | max_drawdown | total_selected_bets |
|------------|---------------------|--------|--------------|---------------------|
| fixed | **-18.78%** | -453,890 | 487,750 | 24,172 |
| half_kelly | -96.79% | -100,000 | 100,000 | 24,172 |
| capped_kelly_0.02 | -23.51% | -99,999.76 | 99,999.76 | 24,172 |
| capped_kelly_0.05 | -47.70% | -99,999.90 | 99,999.90 | 24,172 |

top_n=6 系統では fixed が最良。Kelly 系は資金制約で破綻に近い。

- 実行: `python3 scripts/exp0006_local_opt_topn6_ev105.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42` → outputs/exp0006_local_opt_topn6_ev105.json
