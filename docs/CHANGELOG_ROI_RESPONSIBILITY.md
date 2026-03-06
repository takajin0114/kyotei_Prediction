# 変更差分要約：予測と買い目選定の責務分離・ROI 評価

**実施日**: 2026-03

---

## 何を変えたか

- **評価指標の分離**: hit_rate, mean_reward, ROI（回収率）, 投資額, 払戻額, 的中件数を分解して扱えるようにした。
- **最適化目的の切り替え**: 設定 `evaluation.optimize_for` で `hit_rate` / `mean_reward` / `roi` / `hybrid` を選択可能にした。`hybrid` が従来互換の合成スコア。
- **購入判断の分離**: 予測（候補とスコア）と「何を買うか」を分離し、`tools/betting/` で戦略（1点買い・上位N点・閾値・EV用インターフェース）を切り替えられるようにした。
- **設定の拡張**: `improvement_config.json` に `evaluation`（optimize_for, roi_evaluation_enabled）と `betting`（strategy, top_n, score_threshold, ev_threshold）を追加した。
- **既存互換**: 既存の学習・予測・検証コマンドはデフォルトで従来どおり動作する。

---

## なぜ変えたか

- 的中率と ROI は別問題であり、人気に寄せると hit_rate は上がりやすいが ROI が伸びないことがある。
- 予測モデルの責務は「候補とスコアを出すこと」、買い目選定の責務は「オッズやルールで購入判断すること」に分離したい。
- 学習・評価で ROI を併記・目的にできるようにし、将来 EV ベースの買い目選定へ拡張しやすくするため。

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|----------|----------|
| `docs/ROI_AND_RESPONSIBILITY_SEPARATION.md` | 新規。背景・調査結果・設計方針・変更範囲・今後の拡張を記載。 |
| `docs/CHANGELOG_ROI_RESPONSIBILITY.md` | 本ファイル。変更差分要約。 |
| `kyotei_predictor/pipelines/kyotei_env.py` | `calc_trifecta_payout()` を追加。`step()` の `info` に `payout`, `bet_amount`, `hit` を追加（ROI 評価用）。 |
| `kyotei_predictor/tools/evaluation/metrics.py` | 新規。評価指標の算出と `objective_from_metrics(optimize_for)`。 |
| `kyotei_predictor/tools/evaluation/__init__.py` | metrics の再エクスポートを追加。 |
| `kyotei_predictor/tools/evaluation/evaluate_graduated_reward_model.py` | 指標分離・ROI/投資額/払戻額の出力と JSON への `metrics` 追加。 |
| `kyotei_predictor/tools/betting/__init__.py` | 新規。買い目選定パッケージ。 |
| `kyotei_predictor/tools/betting/strategy.py` | 新規。single / top_n / threshold / ev 戦略と `select_bets()`。 |
| `kyotei_predictor/config/improvement_config.json` | `evaluation`, `betting` セクションを追加。 |
| `kyotei_predictor/config/improvement_config_manager.py` | `get_evaluation_params`, `get_optimize_for`, `get_roi_evaluation_enabled`, `get_betting_*` を追加。 |
| `kyotei_predictor/tools/optimization/optimize_graduated_reward.py` | `evaluate_model` で info から ROI 等を集計し、`optimize_for` に応じて `objective_from_metrics` でスコア算出。 |
| `kyotei_predictor/tools/prediction_tool.py` | `include_selected_bets` オプションと `--include-selected-bets` CLI。設定に基づく `selected_bets` を予測結果に追加。 |
| `docs/PROJECT_LAYOUT.md` | 実行例に ROI 重視・betting 切り替え・検証時の ROI 確認を追記（下記 How to Run と整合）。 |

---

## 何が今後やりやすくなったか

- **ROI を最適化目的にできる**: `evaluation.optimize_for` を `roi` にすると Optuna が ROI を最大化する。
- **評価結果の比較**: 評価 JSON に hit_rate, mean_reward, roi_pct, total_bet, total_payout が含まれるため、指標ごとの比較がしやすい。
- **買い目選定の切り替え**: 設定や CLI で 1点買い・上位N点・閾値などを切り替えられる。将来 EV ベースを追加しやすい。
- **責務の明確化**: 予測は「候補とスコア」、買い目選定は `tools/betting` に分かれたため、EV や確率モデル分離の拡張がしやすい。
