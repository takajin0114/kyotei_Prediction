# EXP-0072b: Race Difficulty Filter Recheck

## 実験目的

EXP-0072 の baseline（CASE0）が EXP-0070 / EXP-0071 の CASE2 と一致していなかったため、**baseline 再現性の差分検証**を行い、原因修正後に difficulty filter 実験を再実行する。

## baseline 差分確認

| 項目 | EXP-0070 CASE2 | EXP-0072 CASE0（修正前） |
|------|----------------|---------------------------|
| ROI | 11.12% | 8.29% |
| total_profit | 5,772 | 4,524 |
| max_drawdown | 8,838 | 9,266 |
| bet_count | 590 | 590 |

- selection は同一（4.50 ≤ EV < 4.75, prob ≥ 0.05）であり bet_count は一致。ROI・profit・max_dd の差は **stake schedule の違い** に起因。

## 差分原因

1. **ref_profit 算出方法の違い**
   - **EXP-0070**: ref_profit を **CASE0（4.30 ≤ EV < 4.75, prob ≥ 0.05）** で算出し、その ref から switch_dd4000 の stake schedule を計算。全 CASE（含む CASE2）でこの schedule を共通利用。
   - **EXP-0072（修正前）**: ref_profit を **CASE2 selection（4.50 ≤ EV < 4.75, prob ≥ 0.05）** で算出していた。そのため ref_profit の値が EXP-0070 と異なり、stake schedule が変わり、結果として ROI・profit・max_drawdown がずれていた。

2. その他の条件は同一
   - prediction 参照先: いずれも `outputs/ev_cap_experiments/rolling_roi_predictions`（calib_sigmoid）
   - rolling window: TRAIN_DAYS=30, TEST_DAYS=7, STEP_DAYS=7, n_windows=36
   - skip_top20pct: 同一（SKIP_TOP_PCT）
   - block 計算: いずれも n_w // 6 で 6 block
   - selection filter: 4.50 ≤ EV < 4.75, prob ≥ 0.05 で同一

## 修正内容

- **run_exp0072_race_difficulty_filter.py**: ref_profit 算出を **EXP-0070 と一致**させるため、**CASE0（4.30, 4.75, 0.05）** で ref_profit を計算するように変更。stake schedule は全 difficulty variant で共通。
- **run_exp0072_baseline_reproduce.py**: EXP-0070 CASE2 と EXP-0072 CASE0 を同条件（同一 prediction・同一 window）で再計算し、ref を「CASE0 で算出」 vs 「CASE2 で算出」の 2 通りで比較。同一 schedule を使えば結果が一致することを確認。
- **run_exp0072b_race_difficulty_recheck.py**: 上記修正を反映した difficulty filter を EXP-0072b として再実行し、`exp0072b_race_difficulty.json` を出力するエントリポイント。

## difficulty filter 再実験結果（EXP-0072b, n_w=36）

ref_profit を CASE0（4.30, 4.75, 0.05）で算出したうえで再実行。

| variant | ROI | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|---------|-----|--------------|--------------|----------------------|-----------|------------------------|
| CASE0 | **11.12%** | **5,772** | **8,838** | **9,783.05** | 590 | 9 |
| CASE1 | -22.78% | -5,836 | 7,050 | -19,918.09 | 293 | 8 |
| CASE2 | -14.35% | -3,316 | 4,850 | -12,560.61 | 264 | 7 |
| CASE3 | 7.68% | 3,362 | 10,648 | 6,764.59 | 497 | 10 |
| CASE4 | -13.24% | -1,358 | 3,308 | -11,606.84 | 117 | 5 |
| CASE5 | -15.52% | -1,440 | 2,848 | -13,584.91 | 106 | 5 |

- **CASE0（baseline）** が EXP-0070 CASE2 と一致（ROI 11.12%, profit 5,772, max_dd 8,838, bet_count 590）。
- いずれの difficulty フィルタ（CASE1〜CASE5）も CASE0 を上回っていない。

## 採用判断

- **reject**。baseline を EXP-0070 と一致させたうえで再評価しても、レース難易度フィルタ（top1_prob / prob_gap / entropy）のいずれも baseline を上回らなかった。主軸は **CASE2 selection（4.50≤EV<4.75, prob≥0.05）＋ difficulty filter なし** のまま維持する。

## 次の考察

- ref_profit / switch_dd4000 の算出は **EXP-0070 と同一**（CASE0: 4.30, 4.75, 0.05）に統一した。今後の同系統実験でもこの仕様を踏襲すること。
- 難易度フィルタは別の閾値・複合条件の検討の余地はあるが、現時点では採用しない。

---

結果 JSON: `outputs/race_difficulty/exp0072b_race_difficulty.json`（outputs は gitignore のため未コミット）。
