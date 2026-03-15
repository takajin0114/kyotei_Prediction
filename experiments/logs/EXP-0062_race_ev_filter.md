# EXP-0062: Race EV Filter Experiment

## 実験目的

レース単位の期待値 **race_ev = Σ(probability × odds)** を計算し、race_ev でレースをフィルタした場合に ROI・利益・リスク指標がどう変化するかを評価する。現在は bet 単位の EV フィルタのみであるため、レース全体の期待値がプラスのレースを選ぶことで ROI 改善が期待できる。

## 実装内容

- 予測: 既存と同様に `predict_proba` → `scores_to_all_combinations` で 120 通りを生成。
- レースごとに **race_ev = Σ(probability × odds)** を算出（オッズは DB/repo から取得）。
- 以下の 5 条件を比較:
  - **CASE0**: baseline（レース EV フィルタなし）
  - **CASE1**: race_ev ≥ 1.00 のレースのみ
  - **CASE2**: race_ev ≥ 1.02
  - **CASE3**: race_ev ≥ 1.05
  - **CASE4**: race_ev ≥ 1.10
- 各 CASE で通過したレースに既存戦略 **d_hi475 + switch_dd4000** を適用（skip_top20pct → 4.30≤EV<4.75 & prob≥0.05、累積 DD≥4000 で stake=80）。
- Rolling validation: **n_windows=12**（既存 EXP と同条件）。

## 実験条件

| 項目 | 値 |
|------|-----|
| n_windows | 12 |
| 戦略 | d_hi475 + switch_dd4000 |
| 予測 | outputs/ev_cap_experiments/rolling_roi_predictions（top_n_ev_gap_filter） |
| DB | kyotei_races.sqlite |
| train_days / test_days / step_days | 30 / 7 / 7 |

## 結果表（n_windows=12）

| variant | ROI | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|---------|-----|--------------|--------------|----------------------|-----------|------------------------|
| CASE0_baseline | 3.29% | 934 | 7,766 | 2,865.03 | 326 | 3 |
| CASE1_race_ev_ge_100 | 3.29% | 934 | 7,766 | 2,865.03 | 326 | 3 |
| CASE2_race_ev_ge_102 | 3.29% | 934 | 7,766 | 2,865.03 | 326 | 3 |
| CASE3_race_ev_ge_105 | 3.29% | 934 | 7,766 | 2,865.03 | 326 | 3 |
| CASE4_race_ev_ge_110 | 3.29% | 934 | 7,766 | 2,865.03 | 326 | 3 |

## 考察

- **全 CASE で同一結果**（ROI 3.29%、total_profit 934、bet_count 326、longest_losing_streak 3）。n_w=12 の対象期間では、オッズが取得できたレースのいずれも race_ev ≥ 1.10 を満たしており、CASE1〜CASE4 のフィルタで除外されるレースがなかったと解釈できる。
- race_ev フィルタの効果を評価するには、**n_windows を 24/30/36 に増やした再実験**や、race_ev の分布（ヒストグラム）を確認し、閾値 1.00〜1.10 で実際に除外されるレース数がどれだけあるかを把握する必要がある。
- 実装は仕様どおり完了。結果 JSON: `outputs/race_ev_filter/exp0062_race_ev_filter_results.json`。

---

- 実行コマンド: `python3 -m kyotei_predictor.tools.run_exp0062_race_ev_filter --n-windows 12`
- 結果 JSON: `outputs/race_ev_filter/exp0062_race_ev_filter_results.json`
