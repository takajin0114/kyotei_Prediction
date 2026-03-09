# Experiment Leaderboard

このファイルは主要実験の比較表を管理する。

## ROI Leaderboard

- **正式 reference (n_w=12)**: 同一条件・n_windows=12 で比較した公式結果。
- **暫定 best (n_w=4 等)**: 少ない window 数のみで未確定。採用前に n_w=12 再評価を要する。

| Rank | Experiment ID | Model | Calibration | Features | Strategy | Parameters | overall_roi_selected | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | EXP-0007 | xgboost | sigmoid | extended_features | top_n_ev | top_n=3, ev=1.18 | **-14.54%** (n_w=12) | EV 高解像度探索で最良（adopt） |
| 2 | EXP-0006 | xgboost | sigmoid | extended_features | top_n_ev | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | **正式 reference**（従来 1 位） |
| 3 | EXP-0007 | xgboost | sigmoid | extended_features | top_n_ev | top_n=4, ev=1.05 | **-17.85%** (n_w=12) | top_n 局所探索で最良（hold） |
| 4 | EXP-0006 | xgboost | sigmoid | extended_features | top_n_ev | top_n=6, ev=1.00 | **-18.78%** (n_w=12) | 正式 reference 周辺の局所最適（adopt） |
| 5 | EXP-0006 | xgboost | sigmoid | extended_features | top_n_ev | top_n=3, ev=1.20 (grid) | -10.94% (n_w=6) | strategy grid; bet sizing capped_0.02 → -8.66% |
| 6 | EXP-0006 | xgboost | sigmoid | extended_features | top_n_ev | top_n=3, ev=1.25 (grid) | -11.15% (n_w=4) | **暫定 best**（n_w=4 のみ・未確定） |
| 7 | EXP-0006 | xgboost | sigmoid | extended_features | top_n_ev | top_n=6, ev=1.05 | -19.71% (n_w=12) | 正式 reference（top_n=6 系統・前回） |
| 8 | EXP-0005 | xgboost | sigmoid | extended_features | top_n_ev | top_n=6, ev=1.20 | -20.7% (n_w=12) | 旧 reference |
| 9 | EXP-0005 | lightgbm | sigmoid | extended_features | top_n_ev | - | -29.9% (n_w=12) | 安定性良好 |
| 10 | EXP-0004 | sklearn baseline | sigmoid | extended_features | top_n_ev | - | -27.7% (n_w=12) | sklearn reference |
| 11 | EXP-0001 | sklearn baseline | sigmoid | extended_features | top_n_ev | - | -28% | 旧 reference |
| - | EXP-0002 | sklearn baseline | sigmoid | extended_features_v2 | top_n_ev | - | -35% (n_w=2) | v2 比較・hold |
| - | EXP-0004 | sklearn baseline | sigmoid | extended_features_v2 | top_n_ev | - | -33.76% (n_w=12) | v2 正式比較・hold |

## EV Threshold Sweep (ev_threshold_only, EXP-0005)

| ev_threshold | overall_roi | mean_roi | median_roi | bet_count | profit | max_drawdown |
|---|---|---|---|---|---|---|
| 1.05 | -48.95% | -49.05 | -50.38 | 212614 | -10,406,510 | 10,406,510 |
| 1.10 | -49.56% | -49.65 | -49.48 | 204223 | -10,121,210 | 10,121,210 |
| 1.15 | -50.83% | -50.95 | -49.52 | 196230 | -9,974,130 | 9,974,130 |
| 1.20 | -51.23% | -51.49 | -51.53 | 188699 | -9,667,800 | 9,667,800 |
| 1.25 | -51.35% | -51.61 | -51.55 | 181616 | -9,325,560 | 9,325,560 |

## Bet Sizing 比較（正式表, n_w=12）

selection 条件ごとの bet sizing 比較。overall_roi_selected / profit / max_drawdown / total_selected_bets を記載。

### 条件: top_n=3, ev=1.18（EXP-0007 Task1 最良・現 1 位）

| bet_sizing | overall_roi_selected | profit | max_drawdown | total_selected_bets |
|------------|---------------------|--------|--------------|---------------------|
| fixed | -14.54% | -224,090 | 279,680 | 15,407 |
| half_kelly | -96.69% | -100,000 | 100,000 | 15,407 |
| capped_kelly_0.02 | -8.17% | -99,999.75 | 274,447 | 15,407 |
| capped_kelly_0.05 | -38.17% | -99,999.91 | 99,999.90 | 15,407 |

### 条件: top_n=3, ev=1.20（正式 reference）

| bet_sizing | overall_roi_selected | profit | max_drawdown | total_selected_bets |
|------------|---------------------|--------|--------------|---------------------|
| fixed | -14.88% | -226,920 | 283,570 | 15,249 |
| half_kelly | -96.69% | -100,000 | 100,000 | 15,249 |
| capped_kelly_0.02 | -8.66% | -99,999.76 | 247,197 | 15,249 |
| capped_kelly_0.05 | -38.11% | -99,999.90 | 99,999.90 | 15,249 |

### 条件: top_n=6, ev=1.00（正式 reference 周辺の局所最適）

| bet_sizing | overall_roi_selected | profit | max_drawdown | total_selected_bets |
|------------|---------------------|--------|--------------|---------------------|
| fixed | -18.78% | -453,890 | 487,750 | 24,172 |
| half_kelly | -96.79% | -100,000 | 100,000 | 24,172 |
| capped_kelly_0.02 | -23.51% | -99,999.76 | 99,999.76 | 24,172 |
| capped_kelly_0.05 | -47.70% | -99,999.90 | 99,999.90 | 24,172 |

### 条件: top_n=6, ev=1.05（EXP-0007 Task1）

| bet_sizing | overall_roi_selected | profit | max_drawdown | bet_count |
|------------|---------------------|--------|--------------|-----------|
| fixed | -19.71% | -462,310 | 493,400 | 23,461 |
| half_kelly | -96.79% | -100,000 | 100,000 | 23,461 |
| capped_kelly_0.02 | -23.92% | -99,999.75 | 99,999.75 | 23,461 |
| capped_kelly_0.05 | -48.01% | -99,999.91 | 99,999.91 | 23,461 |

運用は fixed を推奨（Kelly 系は資金制約で破綻リスクあり）。

## Notes

- **EXP-0006**: (1) **正式 reference (n_w=12)**: 2位 top_n=3, ev=1.20 **-14.88%**（従来 1 位）。top_n=6, ev=1.00 **-18.78%**（局所最適 adopt）。(2) **暫定 best (n_w=4)**: top_n=3, ev=1.25 で -11.15% は window 数少のため未確定。(3) bet sizing は fixed 推奨。ev_threshold_only は **reject**。
- **EXP-0007**: (1) **top_n=3 EV 高解像度探索**: ev=1.18 が **-14.54%** で 1 位（adopt）。ev=1.20 は -14.88%。(2) **bet sizing 正式比較**: 条件 top_n=3, ev=1.18 で fixed -14.54%, capped_kelly_0.02 -8.17%。運用は fixed 推奨。(3) 従来 EXP-0007: top_n=4, ev=1.05 で -17.85%（hold）。calibration 比較は experiments/logs/EXP-0007_strategy_optimization.md。今回の局所探索は experiments/logs/EXP-0007_bet_sizing_and_local_search.md。
- 比較値の出典: overall_roi_selected は rolling_validation_roi の total_payout / total_bet から算出。n_windows=12 は同一条件。
- EXP-0005 ev_threshold_sweep: ev_threshold_only 戦略で threshold 1.05〜1.25 を比較（n_w=6）。最良 ROI は ev=1.05 で -48.95%。
- この表は主に overall_roi_selected で比較する
- 同程度なら安定性（std_roi_selected）も考慮する
- extended_features_v2 は n_windows=12 でも extended_features より ROI 悪化 → hold
- AI は新しい提案をする前に leaderboard を確認すること
