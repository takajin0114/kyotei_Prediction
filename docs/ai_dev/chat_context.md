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
- strategy: top_n_ev_gap_filter
- top_n: 3
- ev_threshold: 1.18
- ev_gap_threshold: 0.05
- seed: 42
- features: extended_features
- validation windows: 12

---

# Best Historical Result (Leaderboard #1)

leaderboard の 1 位。

- strategy: top_n_ev_gap_filter, top_n=3, ev=1.18, ev_gap_threshold=0.05
- ROI: **-13.81%** (n_w=12)
- selected_bets: 14,994（experiments/leaderboard.md の Bet Sizing 表参照）
- validation windows: 12

---

# Latest Experiment

<!-- update_chat_context.py が自動更新 -->

- **最新 EXP**: EXP-0013
- **概要**: EV gap strategy（top_n_ev_gap_filter）。**ev_gap = ev_rank1 - ev_rank2**。ev_gap < threshold ならレースを skip。ev_gap_threshold=0.02,0.03,0.05,0.07 で sweep。ベースライン top_n_ev top_n=3 ev=1.18（-14.54%）と比較。
- **結果**: ev_gap_threshold=0.05 が最良 **-13.81%**（+0.73%pt 改善）。**採用**。詳細は outputs/ev_gap_experiments/exp0013_ev_gap_results.json および experiments/logs/EXP-0013_ev_gap_strategy.md。
- **ログ**: experiments/logs/EXP-0013_ev_gap_strategy.md
- **結果 JSON**: outputs/ev_gap_experiments/exp0013_ev_gap_results.json

# Leaderboard Summary

<!-- update_chat_context.py が自動更新 -->

| Rank | Experiment ID | Parameters | overall_roi_selected | selected_bets | Notes |
|------|----------------|-----------|----------------------|----------------|-------|
| 1 | EXP-0013 | top_n_ev_gap_filter, top_n=3, ev=1.18, ev_gap=0.05 | **-13.81%** (n_w=12) | 14,994 | EV gap で曖昧レース skip（adopt） |
| 2 | EXP-0007 | top_n=3, ev=1.18 | **-14.54%** (n_w=12) | — | EV 高解像度探索で最良（adopt） |
| 3 | EXP-0006 | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | — | **正式 reference**（従来 1 位） |
| 4 | EXP-0007 | top_n=4, ev=1.05 | **-17.85%** (n_w=12) | — | top_n 局所探索で最良（hold） |
| — | EXP-0011 | top_n_ev_prob_pool | ベースライン超えず | — | 採用見送り。 |
| — | EXP-0012 | top_n_ev_power_prob (alpha×top_n×ev) | ベースライン未達 | — | 全条件採用見送り。最良 -26.28%。 |

詳細は experiments/leaderboard.md 参照。

# Current Findings

- **EXP-0013**: top_n_ev_gap_filter（ev_gap=0.05）が新ベスト **-13.81%**（n_w=12）。ev_gap = ev_rank1 - ev_rank2 で曖昧レースを skip すると ROI 改善。
- EV threshold を下げると bet 数が増える。ev=1.18 が従来 1 位（-14.54%）、ev=1.20 が 2 位（-14.88%）。
- top_n が大きいと ROI が悪化する傾向（top_n=3 が最良、top_n=6 で -18.78%）。
- bet sizing は fixed が最良。Kelly 系は資金制約で破綻リスクあり。
- calibration は sigmoid が none より有利（-14.88% vs -15.80%）。
- xgboost が lightgbm より ROI 良好（-14.88% vs -20.90%）。
- EXP-0010: race_filtered_top_n_ev は full grid で全条件ベースライン以下。レースフィルタで bet 数は減るが ROI は未改善。
- EXP-0011: top_n_ev_prob_pool はベースライン（top_n_ev 3/1.18）を超えず採用見送り。
- EXP-0012: top_n_ev_power_prob は全グリッドでベースライン未達。採用見送り。

---

# Open Questions

- EXP-0008 Task3: ensemble（確率平均）で bet_count=0 となる不具合。予測マージ／パス参照の修正が必要。
- 暫定 best（n_w=4）top_n=3, ev=1.25 は n_w=12 再評価が未実施。

---

# Next Experiments

- 現行ベスト戦略: top_n_ev_gap_filter, top_n=3, ev=1.18, ev_gap_threshold=0.05（ROI -13.81%）。EXP-0013 で採用。
- ev_gap_threshold の追加 sweep（0.04, 0.06 等）で局所最適の確認を検討。
- ensemble 不具合修正後の再評価。
- top_n / EV threshold の追加 sweep（必要に応じて）。
- probability calibration の詳細比較（必要に応じて）。
