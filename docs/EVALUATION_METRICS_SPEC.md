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
- **evaluation_mode**: config（`improvement_config.json` の `evaluation.evaluation_mode`）で指定可能。CLI の `--evaluation-mode` を指定した場合は CLI 優先。未指定時は config → 未設定時は `first_only`。比較条件を固定する場合は config に明示することを推奨。
- **推奨出力先**: `outputs/verification_YYYYMMDD_HHMMSS.json`。`--save` で自動作成。`--output` は従来どおり任意パス指定。

---

## 最適化結果 JSON の仕様（optimize_graduated_reward）

最適化スクリプトが保存する結果 JSON（例: `optuna_results/graduated_reward_*.json`）の構造と、比較時に使う指標を定義する。

### トップレベル

| キー | 意味 |
|------|------|
| optimization_time | 最適化完了日時（ISO 形式） |
| study_name | Optuna study 名 |
| **optimize_for** | 最適化の目的指標（下記参照） |
| n_trials | 試行数 |
| total_trials | 実際の trial 数 |
| best_trial | 最良 trial の情報（下記） |
| all_trials | 全 trial のリスト（下記） |

### optimize_for の意味

| 値 | 意味 | objective の取り方 |
|----|------|-------------------|
| hit_rate | 的中率を最大化 | score = hit_rate |
| mean_reward | 平均報酬を最大化 | score = mean_reward |
| roi | 回収率を最大化 | score = roi_pct |
| hybrid | 従来互換の合成スコア | score = hit_rate * 100 + mean_reward / 1000 |

config の `evaluation.optimize_for` で指定。比較時は **同じ optimize_for 同士** で比較すること。

### best_trial に含まれるキー

| キー | 意味 |
|------|------|
| number | trial 番号 |
| value | Optuna の目的関数値（optimize_for に応じたスコア） |
| params | ハイパーパラメータ |
| **optimize_for** | この trial で使った目的指標 |
| **hit_rate** | 的中率（0〜1） |
| **mean_reward** | 平均報酬 |
| **roi_pct** | 回収率（%） |
| **total_bet** | 評価時の投資額合計（円） |
| **total_payout** | 評価時の払戻額合計（円） |
| **hit_count** | 的中件数 |

### all_trials の各要素に含まれるキー

各 trial は少なくとも以下を持つ。user_attrs から格納した分のみ存在する場合あり。

| キー | 意味 |
|------|------|
| number | trial 番号 |
| value | 目的関数値 |
| params | ハイパーパラメータ |
| state | Optuna の状態（COMPLETE 等） |
| hit_rate | 的中率 |
| mean_reward | 平均報酬 |
| roi_pct | 回収率（%） |
| total_bet | 投資額合計（円） |
| total_payout | 払戻額合計（円） |
| hit_count | 的中件数 |
| optimize_for | 目的指標 |

### 指標の定義（最適化結果内）

本ドキュメントの「共通指標の定義」と同一。評価エピソード集計から算出する。

- **hit_rate**: 的中したエピソード数 / n_eval_episodes
- **mean_reward**: エピソード報酬の平均
- **roi_pct**: (total_payout / total_bet) * 100（total_bet > 0 のとき）
- **total_bet**: 評価時のベット額合計（環境の bet_amount 等から集計）
- **total_payout**: 評価時の払戻合計
- **hit_count**: 的中したエピソード数

### どの指標で比較すべきか

- **optimize_for が同じ**結果同士で value（スコア）を比較する。
- **hit_rate / mean_reward / roi_pct** は全 trial に記録してあるので、目的指標以外のトレードオフ（例: roi 最適化で hit_rate がどう変わったか）も確認できる。
- 検証ツール（verify_predictions）の summary と比較する場合は、**evaluation_mode** を揃える（first_only 同士、または selected_bets 同士）。

### A案比較時の注意点

- 最適化は「1本選んで step」する環境での評価なので、検証の「1位に100円賭けた結果」とはスケール・意味が異なる。キー名を揃えてあるので並べて見ることはできるが、**比較は同一条件（同じデータ・同じ evaluation_mode）で行う**こと。
- optimize_for=roi で最適化した場合でも、学習は依然として段階的報酬の PPO。ROI は評価・検証で「見る」指標として使う。

### B案比較時の注意点

- 検証では evaluation_mode=selected_bets にすると、予測の selected_bets に基づく ROI が算出される。買い目選定戦略（single / top_n / threshold / ev）を変えた結果を、同じ evaluation_mode で比較すること。
- 最適化結果の best_trial に roi_pct が入っているので、検証の roi_pct と並べて「学習評価と実予測検証の乖離」を確認できる。

---

## 買い目選定（EV 戦略）

- **strategy=ev**（betting_selector）: 候補に **probability** と **ratio**（または **odds**）がある場合、EV = 確率×オッズ−1 を計算し、**ev_threshold** 以上の組み合わせのみ購入。オッズがない候補は expected_value キーがあればそれで判定（後方互換）。該当なし・オッズなしの場合は **top_n** 点でフォールバック。
- 予測ツールは候補に **ratio** を付与する（オッズあり時）。config の `betting.ev_threshold` で閾値を指定。将来、summary に EV 採用件数や採用基準を残す拡張が可能。

---

## 比較時の注意

- 評価は「学習環境で 1 本選んで step した結果」の集計、検証は「予測 JSON の 1 位に 100 円賭けた結果」の集計。意味は異なるが、**キー名を揃えてあるので、ログや JSON を並べて A/B 比較しやすい**。
- B 案では検証に `selected_bets` ベースの ROI を追加する際、同じキー（`total_bet`, `total_payout`, `roi_pct`）で別の `evaluation_mode` を出す想定。

**最終更新**: 2026-03
