# EXP-0006 局所最適化とドキュメント整合性回復 報告

日付: 2026-03-09

## 1. 変更ファイル一覧

- `scripts/exp0006_local_opt_topn6_ev105.py` — 新規。Task1 top_n=6 ev sweep、Task2 ev=1.05 top_n sweep、Task3 bet sizing。
- `experiments/logs/EXP-0006_strategy_grid.md` — 局所最適化セクション（Task1/2/3 表・実行コマンド）を追加。
- `experiments/leaderboard.md` — 正式/暫定の区別を明記、top_n=6 ev=1.00 を Rank2 に追加、Bet Sizing 比較正式表を追加、Notes 更新。
- `docs/ai_dev/project_status.md` — メイン戦略・EXP-0006 を正式 reference 2本立てと局所最適化結果で更新。
- `docs/ai_dev/chat_context.md` — Run Report・Leaderboard・Project Status・Latest Experiment を EXP-0006 局所最適化ベースに更新。
- `experiments/logs/EXP-0006_local_opt_report_20260309.md` — 本報告（新規）。

## 2. 実行コマンド

```bash
python3 scripts/exp0006_local_opt_topn6_ev105.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42
```

## 3. 実験結果サマリー

### Task1: top_n=6 固定 ev_threshold 再探索 (n_w=12)

| ev_threshold | overall_roi_selected | total_selected_bets | profit | max_drawdown |
|--------------|---------------------|---------------------|--------|--------------|
| 1.00 | **-18.78%** | 24,172 | -453,890 | 453,890 |
| 1.02 | -19.17% | 23,902 | -458,130 | 458,130 |
| 1.05 | -19.71% | 23,461 | -462,310 | 462,310 |
| 1.07 | -19.63% | 23,193 | -455,290 | 455,290 |
| 1.10 | -20.06% | 22,814 | -457,750 | 457,750 |

### Task2: ev=1.05 固定 top_n 近傍 (n_w=12)

| top_n | overall_roi_selected | total_selected_bets | profit | max_drawdown |
|-------|---------------------|---------------------|--------|--------------|
| 5 | -21.92% | 24,744 | -542,460 | 542,460 |
| 6 | **-19.71%** | 23,461 | -462,310 | 462,310 |
| 7 | -20.75% | 25,793 | -535,280 | 535,280 |

### Task3: bet sizing（最良条件 top_n=6, ev=1.00）

| bet_sizing | overall_roi_selected | profit | max_drawdown | total_selected_bets |
|------------|---------------------|--------|--------------|---------------------|
| fixed | **-18.78%** | -453,890 | 487,750 | 24,172 |
| half_kelly | -96.79% | -100,000 | 100,000 | 24,172 |
| capped_kelly_0.02 | -23.51% | -99,999.76 | 99,999.76 | 24,172 |
| capped_kelly_0.05 | -47.70% | -99,999.90 | 99,999.90 | 24,172 |

## 4. 旧 reference との ROI 比較

| 条件 | overall_roi_selected | 備考 |
|------|---------------------|------|
| 正式 reference（top_n=6, ev=1.05, n_w=12） | -19.71% | 今回の局所探索の基準 |
| **局所最適（top_n=6, ev=1.00, n_w=12）** | **-18.78%** | 約 0.93pt 改善 → adopt |
| new reference（top_n=3, ev=1.20, n_w=12） | -14.88% | 全体 1 位のまま |

## 5. 採用判断

- **adopt**: top_n=6, ev_threshold=1.00 を正式 reference（top_n=6 系統）の更新として採用（-18.78%, 旧 ev=1.05 の -19.71% より約 0.9pt 改善）。
- **hold**: 暫定 best（n_w=4）の top_n=3, ev=1.25（-11.15%）は window 数少のため未確定のまま。
- **reject**: ev_threshold_only は従来どおり reject。
- bet sizing: 運用は **fixed** 推奨。Bet Sizing 正式表は leaderboard に追加済み。
