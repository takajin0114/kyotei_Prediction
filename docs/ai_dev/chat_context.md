# Chat Context

AI レビュー用。実験結果 push のたびに `python3 -m kyotei_predictor.tools.update_chat_context` で **Latest Experiment** と **Leaderboard Summary** を更新すること。

---

# Project Overview

- **現在の目的**: ROI 最大化（rolling validation n_w=12 における overall_roi_selected の改善）。
- **評価**: extended_features、rolling validation、selected_bets で検証。

---

# Current Strategy

| 項目 | 値 |
|------|-----|
| model | xgboost |
| calibration | sigmoid |
| strategy | top_n_ev |
| top_n | 3 |
| ev_threshold | 1.20（正式 reference）。1 位条件は ev=1.18（-14.54%） |
| seed | 42 |
| features | extended_features |
| n_windows | 12 |

※ 詳細は docs/ai_dev/project_status.md 参照。

---

# Latest Experiment

<!-- update_chat_context.py が自動更新 -->

- **最新 EXP**: EXP-0008
- **概要**: 正式 reference（xgboost, sigmoid, extended_features, top_n_ev, top_n=3, ev=1.20, ROI -14.88%）を前提に、(1) fractional Kelly キャップのスイープ、(2) calibration none vs sigmoid の比較、(3) xgboost / lightgbm / ensemble（確率平均）の EV 比較を行う。
- **結果**: - **Task1**: fractional Kelly cap 0.01 で ROI 最良（-6.99%）だが資金制約で破綻に近い。運用は fixed 推奨。 - **Task2**: calibration は sigmoid を採用（-14.88%）。none は -15.80%。 - **Task3**: xgboost > lightgbm。ensemble は不具合のため再実装・再評価が必要。
- **ログ**: experiments/logs/EXP-0008_fractional_kelly.md

# Leaderboard Summary

<!-- update_chat_context.py が自動更新 -->

| Rank | Experiment ID | Parameters | overall_roi_selected | selected_bets | Notes |
|------|----------------|-----------|----------------------|----------------|-------|
| 1 | EXP-0007 | top_n=3, ev=1.18 | **-14.54%** (n_w=12) | — | EV 高解像度探索で最良（adopt） |
| 2 | EXP-0006 | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | — | **正式 reference**（従来 1 位） |
| 3 | EXP-0007 | top_n=4, ev=1.05 | **-17.85%** (n_w=12) | — | top_n 局所探索で最良（hold） |

詳細は experiments/leaderboard.md 参照。

# Open Questions

- EXP-0008 Task3: ensemble（確率平均）で bet_count=0 となる不具合。予測マージ／パス参照の修正が必要。
- 暫定 best（n_w=4）top_n=3, ev=1.25 は n_w=12 再評価が未実施。

---

# Next Experiments

- ensemble 不具合修正後の再評価。
- その他 ROI 改善のための selection / bet sizing の追加実験（leaderboard と project_status を都度確認）。
