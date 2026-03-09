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

**EXP-0008**

実験内容
正式 reference（xgboost, sigmoid, extended_features, top_n_ev, top_n=3, ev=1.20, ROI -14.88%）を前提に、(1) fractional Kelly キャップのスイープ、(2) calibration none vs sigmoid の比較、(3) xgboost / lightgbm / ensemble（確率平均）の EV 比較を行う。

結果
- **Task1**: fractional Kelly cap 0.01 で ROI 最良（-6.99%）だが資金制約で破綻に近い。運用は fixed 推奨。 - **Task2**: calibration は sigmoid を採用（-14.88%）。none は -15.80%。 - **Task3**: xgboost > lightgbm。ensemble は不具合のため再実装・再評価が必要。

結論
ROI のみ見ると cap=0.01 が最良（-6.99%）。いずれも資金制約で profit が約 -10 万に張り付いており、運用は fixed 推奨。fractional Kelly はリスク抑制効果はあるが破綻リスクは残る。

ログ: experiments/logs/EXP-0008_fractional_kelly.md


---

# Leaderboard Summary

| EXP | strategy | ROI | bets |
|-----|----------|-----|------|
| EXP-0007 | top_n=3, ev=1.18 | **-14.54%** (n_w=12) | — |
| EXP-0006 | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | — |
| EXP-0007 | top_n=4, ev=1.05 | **-17.85%** (n_w=12) | — |
| EXP-0006 | top_n=6, ev=1.00 | **-18.78%** (n_w=12) | — |
| EXP-0006 | top_n=3, ev=1.20 (grid) | -10.94% (n_w=6) | — |

詳細は experiments/leaderboard.md 参照。

---

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

- ensemble 不具合修正後の再評価。
- top_n / EV threshold の追加 sweep（必要に応じて）。
- probability calibration の詳細比較（必要に応じて）。
