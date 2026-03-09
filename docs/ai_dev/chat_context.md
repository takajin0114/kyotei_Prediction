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

- **最新 EXP**: EXP-0010
- **概要**: ROI 改善のため、レース単位のフィルタを追加した selection strategy「race_filtered_top_n_ev」を導入し、ベースライン top_n_ev と比較する。レース指標（race_max_ev, race_prob_gap_top1_top2, race_entropy, candidate_count_above_threshold）でフィルタし、通過レースのみ top_n_ev で買い目選定する。
- **結果**: （結果は experiments/logs/ を参照）
- **ログ**: experiments/logs/EXP-0010_race_filter_selection.md

# Leaderboard Summary

<!-- update_chat_context.py が自動更新 -->

| Rank | Experiment ID | Parameters | overall_roi_selected | selected_bets | Notes |
|------|----------------|-----------|----------------------|----------------|-------|
| 1 | EXP-0007 | top_n=3, ev=1.18 | **-14.54%** (n_w=12) | — | EV 高解像度探索で最良（adopt） |
| 2 | EXP-0006 | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | — | **正式 reference**（従来 1 位） |
| 3 | EXP-0007 | top_n=4, ev=1.05 | **-17.85%** (n_w=12) | — | top_n 局所探索で最良（hold） |

詳細は experiments/leaderboard.md 参照。

# Current Findings

- EV threshold を下げると bet 数が増える。ev=1.18 が 1 位（-14.54%）、ev=1.20 が 2 位（-14.88%）。
- top_n が大きいと ROI が悪化する傾向（top_n=3 が最良、top_n=6 で -18.78%）。
- bet sizing は fixed が最良。Kelly 系は資金制約で破綻リスクあり。
- calibration は sigmoid が none より有利（-14.88% vs -15.80%）。
- xgboost が lightgbm より ROI 良好（-14.88% vs -20.90%）。

---

# Open Questions

- EXP-0008 Task3: ensemble（確率平均）で bet_count=0 となる不具合。予測マージ／パス参照の修正が必要。
- 暫定 best（n_w=4）top_n=3, ev=1.25 は n_w=12 再評価が未実施。

---

# Next Experiments

- EXP-0010: race_filtered_top_n_ev のフルグリッド実行（--quick なし）でパラメータ最良組み合わせの探索。
- ensemble 不具合修正後の再評価。
- top_n / EV threshold の追加 sweep（必要に応じて）。
- probability calibration の詳細比較（必要に応じて）。
