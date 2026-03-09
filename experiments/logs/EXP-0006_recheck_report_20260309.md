# EXP-0006 n_w=12 正式再評価 報告

日付: 2026-03-09

## 1. 変更ファイル一覧

- `experiments/logs/EXP-0006_strategy_grid.md` — 正式結果サマリに再評価実行コマンド・出力参照を追記
- `experiments/leaderboard.md` — Notes に暫定ベスト(ev=1.25)の n_w=12 再評価と ev=1.20 最良の経緯を追記
- `docs/ai_dev/project_status.md` — EXP-0006 に暫定ベスト n_w=12 結果と再評価実行日を統合
- `docs/ai_dev/chat_context.md` — Generated At 更新、Run Report（実行コマンド・結果）、Latest Experiment 日付・要約を更新
- `outputs/exp0006_recheck_n12.json` — 再評価結果（gitignore のためコミット対象外）

## 2. 実行コマンド

```bash
cd /path/to/kyotei_Prediction
python3 scripts/exp0006_recheck_topn3_ev125_n12.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42
```

## 3. 実験結果サマリー

### Task1: top_n=3, ev_threshold=1.25（n_w=12 単体）

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

### Task2: top_n=3 固定 EV threshold 微調整（n_w=12）

| ev_threshold | overall_roi_selected | total_bets | profit | max_drawdown |
|--------------|---------------------|------------|--------|--------------|
| 1.20 | **-14.88%** | 15,249 | -226,920 | 246,340 |
| 1.22 | -15.13% | 15,121 | -228,770 | 248,690 |
| 1.25 | -15.05% | 14,920 | -224,540 | 245,110 |
| 1.27 | -15.63% | 14,795 | -231,190 | 250,950 |
| 1.30 | -15.24% | 14,614 | -222,780 | 242,750 |

**最良: ev=1.20**（-14.88%）

### Task3: bet sizing 比較（最良条件 top_n=3, ev=1.20, n_w=12）

| bet_sizing | overall_roi_selected | profit | max_drawdown | total_selected_bets |
|------------|---------------------|--------|--------------|---------------------|
| fixed | -14.88% | -226,920 | 283,570 | 15,249 |
| half_kelly | -96.69% | -100,000 | 100,000 | 15,249 |
| capped_kelly_0.02 | **-8.66%** | -99,999.76 | 247,197 | 15,249 |
| capped_kelly_0.05 | -38.11% | -99,999.90 | 99,999.90 | 15,249 |

## 4. 旧 reference との ROI 比較

| 条件 | overall_roi_selected | 備考 |
|------|---------------------|------|
| 旧 reference (EXP-0005) | -20.7% | top_n=6, ev=1.20, n_w=12 |
| 暫定ベスト (n_w=4) | -11.15% | top_n=3, ev=1.25 |
| 今回 Task1 (ev=1.25, n_w=12) | -15.05% | 暫定を n_w=12 で再評価 |
| **new reference (ev=1.20, n_w=12)** | **-14.88%** | top_n=3, ev=1.20 |

- 旧 reference 比: **約 5.8pt 改善**（-20.7% → -14.88%）
- top_n=3, ev=1.25 は n_w=12 では -15.05% のため、ev 微調整で **ev=1.20 を採用**

## 5. 採用判断

- **adopt**: top_n=3, ev_threshold=1.20 を **new reference** として採用（n_w=12 で -14.88%）
- bet sizing: 運用は **fixed** を推奨（capped_kelly_0.02 は ROI 最良だが資金制約で破綻リスクあり）
