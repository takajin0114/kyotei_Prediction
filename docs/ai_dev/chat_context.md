# Chat Context

AI レビュー用。実験・leaderboard 更新後に `python3 scripts/generate_chat_context.py` で再生成すること。

---

# Project Goal

競艇予測AIのROI最大化（rolling validation n_w=12 における overall_roi_selected の改善）。

---

# Current Production Strategy

現在採用している戦略（leaderboard #1 に基づく）。

- model: xgboost
- calibration: sigmoid
- strategy: top_n_ev
- top_n: 3
- ev_threshold: 1.18
- seed: 42
- features: extended_features
- validation windows: 12

---

# Best Historical Result (Leaderboard #1)

leaderboard の 1 位。

- strategy: top_n=3, ev=1.18
- ROI: **-14.54%** (n_w=12)
- selected_bets: —（experiments/leaderboard.md の Bet Sizing 表参照）
- validation windows: 12

---

# Latest Experiment

<!-- update_chat_context.py が自動更新 -->

- **最新 EXP**: EXP-0012
- **概要**: EV スコアの再設計。**EV_adj = (pred_prob ** alpha) * odds** でスコア化し、ev_threshold 以上から top_n を選ぶ戦略「top_n_ev_power_prob」を評価。alpha=0.7,0.8,0.9,1.0,1.1 × top_n=2,3 × ev=1.15,1.17,1.18,1.19,1.20。ベースライン top_n_ev top_n=3 ev=1.18（-14.54%）と比較。
- **結果**: 結果は **outputs/power_prob_experiments/exp0012_power_prob_results.json** を参照。ベースライン比較は JSON の baseline_diff_roi。結論・採用判断は experiments/logs/EXP-0012_power_prob_ev.md に追記。
- **ログ**: experiments/logs/EXP-0012_power_prob_ev.md
- **結果 JSON**: outputs/power_prob_experiments/exp0012_power_prob_results.json

# Leaderboard Summary

<!-- update_chat_context.py が自動更新 -->

| Rank | Experiment ID | Parameters | overall_roi_selected | selected_bets | Notes |
|------|----------------|-----------|----------------------|----------------|-------|
| 1 | EXP-0007 | top_n=3, ev=1.18 | **-14.54%** (n_w=12) | — | EV 高解像度探索で最良（adopt） |
| 2 | EXP-0006 | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | — | **正式 reference**（従来 1 位） |
| 3 | EXP-0007 | top_n=4, ev=1.05 | **-17.85%** (n_w=12) | — | top_n 局所探索で最良（hold） |
| — | EXP-0011 | top_n_ev_prob_pool | ベースライン超えず | — | 採用見送り。 |
| — | EXP-0012 | top_n_ev_power_prob (alpha×top_n×ev) | JSON 参照 | — | EV_adj=(prob^alpha)*odds。exp0012_power_prob_results.json。 |

詳細は experiments/leaderboard.md 参照。

# Current Findings

- EV threshold を下げると bet 数が増える。ev=1.18 が 1 位（-14.54%）、ev=1.20 が 2 位（-14.88%）。
- top_n が大きいと ROI が悪化する傾向（top_n=3 が最良、top_n=6 で -18.78%）。
- bet sizing は fixed が最良。Kelly 系は資金制約で破綻リスクあり。
- calibration は sigmoid が none より有利（-14.88% vs -15.80%）。
- xgboost が lightgbm より ROI 良好（-14.88% vs -20.90%）。
- EXP-0010: race_filtered_top_n_ev は full grid で全条件ベースライン以下。レースフィルタで bet 数は減るが ROI は未改善。
- EXP-0011: top_n_ev_prob_pool はベースライン（top_n_ev 3/1.18）を超えず採用見送り。

---

# Open Questions

- EXP-0008 Task3: ensemble（確率平均）で bet_count=0 となる不具合。予測マージ／パス参照の修正が必要。
- 暫定 best（n_w=4）top_n=3, ev=1.25 は n_w=12 再評価が未実施。

---

# Next Experiments

- EXP-0011: prob_pool はベースラインを超えず採用見送り。EXP-0012: EV スコア再設計（power_prob）の結果に基づく採用判断。ベースラインを上回れば leaderboard 更新、上回らなければ別の EV 設計や別軸の実験。
- ensemble 不具合修正後の再評価。
- top_n / EV threshold の追加 sweep（必要に応じて）。
- probability calibration の詳細比較（必要に応じて）。
