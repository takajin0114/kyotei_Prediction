# 評価・検証の指標定義（共通基盤）

**目的**: 評価ツール（evaluate_graduated_reward_model）と検証ツール（verify_predictions）で、A/B 比較可能な同一キー・同一意味を揃える。  
**参照**: [IMPLEMENTATION_TASK_LIST_A_TO_B.md](IMPLEMENTATION_TASK_LIST_A_TO_B.md) タスク 1.1 / 1.2 / 1.4

---

## 共通指標の定義

| キー | 意味 | 単位 | 備考 |
|------|------|------|------|
| **hit_rate** | 的中率（的中件数 / レース数） | 0〜1 | 評価では n_episodes あたり、検証では races_with_result あたり |
| **hit_count** | 的中した件数 | 整数 | 評価では「1本選んで的中」、検証では「1位予想が的中」 |
| **mean_reward** | 平均報酬 | スカラー | 評価時のみ（環境の step 報酬の平均） |
| **total_bet** | 投資額の合計 | 円 | 1レースあたり 100 円 × レース数など |
| **total_payout** | 払戻額の合計 | 円 | 的中時のオッズ×賭け金の合計 |
| **roi_pct** | 回収率 | % | (total_payout / total_bet) * 100。total_bet=0 のときは 0 |

評価（evaluate_graduated_reward_model）の `metrics` および検証（verify_predictions）の `summary` では、上記のキーを同じ名前で出す。検証の「1位に100円賭けた場合」は summary に `hit_count`, `total_bet`, `total_payout`, `roi_pct` を入れ、`evaluation_mode: "first_only"` で区別する。

---

## 評価ツールの出力

- **evaluate_graduated_reward_model**: 実行結果の `statistics` および `metrics` に、上記のほか `std_reward`, `n_episodes` を含む。
- **optimize_graduated_reward** 内 **evaluate_model**: 返り値の辞書に `hit_rate`, `mean_reward`, `roi_pct`, `total_bet`, `total_payout`, `hit_count`, `n_episodes` を含む。`optimize_for` に応じて objective を組み立てる。

---

## 検証ツールの出力

- **verify_predictions**: `run_verification` の返り値 `summary` に、従来キーに加え `hit_count`, `total_payout`, `roi_pct`, `evaluation_mode` を含む。
- **推奨出力先**: `outputs/verification_YYYYMMDD_HHMMSS.json`。`--save` で自動作成。`--output` は従来どおり任意パス指定。

---

## 比較時の注意

- 評価は「学習環境で 1 本選んで step した結果」の集計、検証は「予測 JSON の 1 位に 100 円賭けた結果」の集計。意味は異なるが、**キー名を揃えてあるので、ログや JSON を並べて A/B 比較しやすい**。
- B 案では検証に `selected_bets` ベースの ROI を追加する際、同じキー（`total_bet`, `total_payout`, `roi_pct`）で別の `evaluation_mode` を出す想定。

**最終更新**: 2026-03
