# EXP-0071 最終報告

## 1. 変更ファイル一覧

| 種別 | パス |
|------|------|
| 新規 | `kyotei_predictor/tools/run_exp0071_case2_robustness_check.py` |
| 新規 | `experiments/logs/EXP-0071_case2_robustness_check.md` |
| 更新 | `experiments/leaderboard.md`（EXP-0071 行・Notes 追記） |
| 更新 | `docs/ai_dev/chat_context.md`（Latest Experiment を EXP-0071 に更新） |
| 更新 | `docs/ai_dev/project_status.md`（EXP-0071 行追加） |
| 新規 | `docs/ai_dev/EXP-0071_final_report.md`（本報告） |

出力 JSON: `outputs/case2_robustness/exp0071_case2_robustness.json` は **gitignore のため未コミット**。

## 2. DB存在確認

- **パス**: `kyotei_predictor/data/kyotei_races.sqlite`（リポジトリルート基準）
- **確認結果**: 存在確認済み。ツール起動時にも `_resolve_db_path()` で解決し `exists()` をチェックしており、本実行ではデフォルトパスで正常に参照した。

## 3. 実装内容

- **目的**: EXP-0070 採用 CASE2（4.50 ≤ EV < 4.75, prob ≥ 0.05）が **n_windows に依存しないか** を確認する再現性・頑健性評価。
- **ツール**: `run_exp0071_case2_robustness_check.py`
  - EXP-0070 の selection（`_filter_bets_by_selection`）・stake 計算（CASE0 の ref_profit で switch_dd4000 スケジュール算出）・rolling 予測参照（`outputs/ev_cap_experiments/rolling_roi_predictions`）を踏襲。
  - 比較: CASE0（4.30≤EV<4.75）, CASE2（4.50≤EV<4.75）, CASE3（4.30≤EV<4.70）、いずれも prob≥0.05。
  - horizon: n_windows = 24, 30, 36 の 3 通りで実行。
  - 出力: `outputs/case2_robustness/exp0071_case2_robustness.json` に variant / n_windows / ROI / total_profit / max_drawdown / profit_per_1000_bets / bet_count / longest_losing_streak / block_profit を格納。

## 4. 実験条件

- calibration: sigmoid  
- risk control: switch_dd4000  
- skip_top20pct: 0.2（EXP-0070 と同一）  
- switch_dd4000 の stake スケジュール: CASE0 の ref_profit で算出し全 CASE で共通  
- 予測: 既存 calib_sigmoid rolling 予測（`outputs/ev_cap_experiments/rolling_roi_predictions`）を使用  

## 5. 実験結果

| variant | n_w | ROI | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|---------|-----|-----|--------------|--------------|----------------------|-----------|------------------------|
| CASE0 | 24 | 18.24% | 11,744 | 7,766 | 16,681.82 | 704 | 4 |
| CASE2 | 24 | **30.10%** | 11,036 | **6,698** | **27,452.74** | 402 | 7 |
| CASE3 | 24 | 23.22% | **13,386** | 7,730 | 21,247.62 | 630 | 4 |
| CASE0 | 30 | 6.04% | 4,796 | 10,702 | 5,419.21 | 885 | 4 |
| CASE2 | 30 | **15.34%** | 6,908 | **6,698** | **13,706.35** | 504 | 7 |
| CASE3 | 30 | 10.30% | **7,282** | 9,122 | 9,252.86 | 787 | 4 |
| CASE0 | 36 | 0.53% | 484 | 15,886 | 469.45 | 1,031 | 4 |
| CASE2 | 36 | **11.12%** | **5,772** | **8,838** | **9,783.05** | 590 | 9 |
| CASE3 | 36 | 5.45% | 4,410 | 12,866 | 4,819.67 | 915 | 4 |

## 6. 評価

- **CASE2 vs CASE0**: ROI・max_drawdown・profit_per_1000_bets は **全 horizon（24/30/36）で CASE2 が優位**。total_profit は n_w=30, 36 で CASE2 優位、**n_w=24 では CASE0（11,744）> CASE2（11,036）**。
- **CASE2 vs CASE3**: n_w=24/30 では total_profit は CASE3 が最大。n_w=36 では CASE2 が ROI・total_profit・max_dd・profit/1k で優位。
- **採用判断ルール**: 「CASE2 が複数 horizon で優位なら strict evaluation 主軸として採用可能。36 のみ優位なら条件付き採用」に照らすと、total_profit では 30 と 36 の 2 horizon で CASE2 が CASE0 を上回るが、24 では CASE0/CASE3 に及ばない。**判定: 条件付き採用**。n_w=36 を標準とする場合は CASE2 を主軸としてよい。n_w=24 を主に使う場合は total_profit 重視なら CASE0 または CASE3 の選択もあり得る。

## 7. leaderboard 更新内容

- **EXP-0071** を **robustness validation** として 1 行追加（最高 ROI のみでの更新は行っていない）。
- Notes に「CASE2 は全 horizon で ROI・max_dd・profit/1k 優位。n_w=24 では total_profit は CASE0/CASE3 に及ばず。条件付き採用」「結果 JSON は gitignore のため未コミット」を記載。

## 8. 次の考察

- n_w=24 で total_profit を伸ばしたい場合は CASE0 または CASE3 の併用・horizon 別切り替えの検討。
- CASE2 の longest_losing_streak（7〜9）が CASE0/CASE3（4）より長いため、リスク許容に応じた運用・モニタリングの継続。
- EXP-0070 の CASE2 は **n_windows に特化した局所最適ではなく**、複数 horizon で効率・リスク指標が安定して優位であることを本実験で確認した。

---

## 経営判断まとめ

- **CASE2（4.50≤EV<4.75, prob≥0.05）** は、ROI・max_drawdown・profit_per_1000_bets の 3 指標で **n_w=24, 30, 36 のすべてで CASE0 を上回り**、n_windows 依存性は強くない（再現性・頑健性は確認された）。
- **total_profit** に限ると、n_w=24 では CASE0/CASE3 の方が高く、n_w=30/36 では CASE2 が優位。
- **結論**: strict evaluation の主軸としては **条件付き採用**。評価 horizon を n_w=36 に置く場合は CASE2 を主軸としてよい。短期（n_w=24）で絶対利益を優先する場合は CASE0 または CASE3 の選択を許容する運用が妥当。
