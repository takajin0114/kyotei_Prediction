# EXP-0065 最終報告

## 目的

Probability calibration の違い（none / sigmoid / isotonic）が ROI・total_profit・max_drawdown 等に与える影響を検証し、ROI 改善の有無を評価する。

## 条件

| 項目 | 内容 |
|------|------|
| **CASE0** | no calibration |
| **CASE1** | sigmoid calibration |
| **CASE2** | isotonic calibration |
| **戦略** | d_hi475 + switch_dd4000 |
| **Validation** | rolling validation, n_windows = 36 |
| **フィルタ** | race_selected_ev 制約なし（baseline） |

## 出力指標

ROI / total_profit / max_drawdown / profit_per_1000_bets / bet_count / longest_losing_streak

## 結果（n_windows=36）

| variant                 | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|-------------------------|---------|--------------|--------------|----------------------|-----------|------------------------|
| CASE0_no_calibration    | -11.71% | -27,982     | 33,992       | -9,427.9             | 2,968     | 6                     |
| CASE1_sigmoid           | **0.53%** | **484**   | 15,886       | **469.45**           | 1,031     | 4                     |
| CASE2_isotonic         | -22.22% | -61,704     | 65,264       | -18,261.02           | 3,379     | 6                     |

- **ファイル**: `outputs/calibration_comparison/exp0065_calibration_results.json`

## 結論

- **sigmoid 維持（adopt）**。CASE1_sigmoid のみ黒字（ROI 0.53%、total_profit 484）。none は -11.71%、isotonic は -22.22% でいずれも赤字。
- n_w=36 でも EXP-0029（n_w=12）と同様に sigmoid が最良のため、現行の **sigmoid calibration を継続採用** する。

## 更新したドキュメント

- `experiments/leaderboard.md` … EXP-0065 行を追加
- `docs/ai_dev/chat_context.md` … 最新 EXP を EXP-0065 に、Leaderboard Summary と Recent に EXP-0065 を追加
- `docs/ai_dev/project_status.md` … EXP-0065 を追加

## ログ

- `experiments/logs/EXP-0065_calibration_comparison.md`
