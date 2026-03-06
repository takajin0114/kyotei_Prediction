# 予測と買い目選定の責務分離・ROI 重視への方針

**更新**: 2026-03

---

## 1. 背景と目的

### 1.1 現状の課題

- 本プロジェクトは **3連単120通りを直接 action とする PPO 学習**が中心である。
- 学習・最適化は **graduated reward（段階的報酬）** を前提にしている。
- **ROI（回収率）を上げること**と**的中率を上げること**は同義ではない。
  - 人気サイドを当てにいくと hit_rate は上がりやすいが、オッズが低く ROI が伸びない可能性が高い。
- そのため、「予測そのもの」と「どの買い目を買うか」を分離し、将来的に **EV ベースの買い目選定**へ発展できる構成にしたい。

### 1.2 今回の変更範囲

- **全面刷新は行わない。** 既存の PPO + 段階的報酬の資産を活かす。
- 以下を整備する：
  1. **学習目的（reward / objective）** と **評価指標** の分離
  2. **評価指標** の分離（hit_rate, mean_reward, ROI, 投資額, 払戻額, 的中件数）
  3. **予測出力** と **購入判断ロジック** の責務分離
  4. **設定** による reward / optimize_for / betting strategy の切り替え
  5. **ドキュメント** の更新

---

## 2. 既存コードの調査結果（要約）

### 2.1 学習の入口

| 種別 | パス | 説明 |
|------|------|------|
| 本流（Optuna） | `kyotei_predictor/tools/optimization/optimize_graduated_reward.py` | `optimize_graduated_reward()` 内で PPO.learn()。目的関数は `hit_rate * 100 + mean_reward / 1000` の合成スコア。 |
| 直接訓練 | `kyotei_predictor/tools/batch/train_with_graduated_reward.py` | PPO.learn() で学習。 |
| Colab 一括 | `scripts/run_colab_learning_cycle.py` | 内部で optimize_graduated_reward を subprocess 起動。 |

### 2.2 評価の入口

| パス | 説明 |
|------|------|
| `kyotei_predictor/tools/evaluation/evaluate_graduated_reward_model.py` | 学習済み PPO を n_eval_episodes で評価。mean_reward, hit_rate 等を JSON 出力。 |
| `optimize_graduated_reward.py` 内 `evaluate_model()` | トライアルごとに hit_rate, mean_reward を返し、**合成スコア**で Optuna の objective を計算。 |
| `kyotei_predictor/tools/verify_predictions.py` | 予測 JSON と race_data を照合。1位/Top3/Top10/Top20 的中率、**ROI（1位に100円賭けた場合）** を算出。 |

### 2.3 予測の入口

| パス | 説明 |
|------|------|
| `kyotei_predictor/tools/prediction_tool.py` | `predict_races()`, `run_complete_prediction()`。120通りを `predict_trifecta_probabilities_from_data()` で算出し、`all_combinations` として返す。 |

### 2.4 報酬計算の場所

| パス | 内容 |
|------|------|
| `kyotei_predictor/pipelines/kyotei_env.py` | `calc_trifecta_reward()`: action・着順・odds・bet_amount から段階的報酬を計算。`KyoteiEnv.step()` で使用。 |
| `kyotei_predictor/config/improvement_config_manager.py` | `get_reward_params(phase)` で win_multiplier, partial_* 等を取得。 |

### 2.5 購入提案・買い目決定（予測と混在している箇所）

| パス | 内容 |
|------|------|
| `prediction_tool.py` | **予測**は `predict_trifecta_probabilities_from_data()` で 120 通りとスコアを出力。**購入提案**は `generate_purchase_suggestions(top_20_combinations)` で、上位20を前提に流し・ワイド・ボックス・フォーメーション等を組み上位8件を返す。 |
| 混在の整理 | 「どの組み合わせを買うか」の判断が、**上位20を固定で使う**形で prediction_tool 内にあり、**1点買い／上位N点／閾値／EV** などの戦略が設定で切り替えられない。 |

---

## 3. 設計方針の明文化

### 3.1 的中率最適化と ROI 最適化は別問題

- **的中率**は「予測が当たった割合」であり、人気に寄せると上がりやすい。
- **ROI**は「投資額に対する払戻の割合」であり、オッズの高い買い目を選ぶ必要がある。
- 学習報酬と最終評価指標は一致している方が望ましいが、段階的移行でもよい。当面は既存 PPO を残しつつ、**評価側で ROI を併記**し、**optimize_for** で目的を切り替えられるようにする。

### 3.2 予測モデルの責務

- **候補とスコア（確率・ランク）を出すこと**まで。
- 「何を買うか」は予測モジュールの責務外とする。

### 3.3 買い目選定の責務

- **オッズやルールを使って購入判断すること**。
- 例: 常に1点買い、上位N点買い、スコア閾値以上のみ買う。将来は EV ベースに置き換えやすいインターフェースにする。

### 3.4 学習報酬と評価指標

- 学習報酬は従来どおり段階的報酬（improvement_config の reward_design）でよい。
- 評価時は **hit_rate, mean_reward, ROI, 投資額, 払戻額, 的中件数** を分解して保持し、**optimize_for**（hit_rate / mean_reward / roi / hybrid）で最終 objective の組み立てを切り替える。
- **hybrid** の場合のみ、従来互換の合成スコア（例: hit_rate * 100 + mean_reward / 1000）を許可する。

### 3.5 当面の拡張ポイント

- 既存の学習コマンド・予測コマンド・検証コマンドは維持する。
- 設定で **reward_mode**, **optimize_for**, **betting strategy**, **top_n**, **score_threshold**, **ROI 評価の ON/OFF** を切り替え可能にする。
- 将来 EV ベースや確率モデル分離へ進化できる構造にしておく。

---

## 4. 今回の変更範囲（実装）

- **評価指標の分離**: `tools/evaluation/metrics.py` で hit_rate, mean_reward, ROI, 投資額, 払戻額, 的中件数を算出・保持。optimize_for に応じて objective を組み立て。
- **購入判断の分離**: `tools/betting/` に betting strategy を定義。1点買い・上位N点・閾値。EV は将来拡張用のインターフェースのみ。
- **設定の拡張**: `improvement_config.json` および `ImprovementConfigManager` に optimize_for, reward_mode, betting 関連を追加。
- **既存互換**: 既存コマンドはデフォルト設定で従来挙動を維持。optimize_for 未指定時は hybrid（従来スコア）とする。

---

## 5. 今後の拡張ポイント

- **EV ベースの買い目選定**: 確率とオッズから EV を計算し、閾値以上のみ購入する strategy の追加。
- **確率モデルと policy の分離**: 予測を「確率分布」として出力し、買い目選定は別モジュールで行う構成への発展。
- **学習目的の ROI 直接最適化**: 報酬設計を ROI に近づける、または評価指標を ROI にした上での Optuna 最適化。

---

## 6. 関連ドキュメント

- 実行方法・コマンド例: [PROJECT_LAYOUT.md](PROJECT_LAYOUT.md)、[RUN_VERIFICATION.md](RUN_VERIFICATION.md)
- 変更差分の要約: [CHANGELOG_ROI_RESPONSIBILITY.md](CHANGELOG_ROI_RESPONSIBILITY.md)

## 7. テスト

- `kyotei_predictor/tests/test_evaluation_metrics.py`: 評価指標の分離、optimize_for の切り替え
- `kyotei_predictor/tests/test_betting_strategy.py`: 買い目選定の single / top_n / threshold

プロジェクトルートで `pytest kyotei_predictor/tests/test_evaluation_metrics.py kyotei_predictor/tests/test_betting_strategy.py -v` を実行（要 numpy / pytest 環境）。
