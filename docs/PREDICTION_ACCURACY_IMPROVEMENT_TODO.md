# 予測精度向上 — やること整理

**目的**: 3連単予測の的中率・回収率を上げるために、やることを優先度・フェーズ別に整理する。  
**参照**: [trifecta_improvement_strategy.md](trifecta_improvement_strategy.md), [improvement_implementation_summary.md](improvement_implementation_summary.md), [LEARNING_AND_PREDICTION_STATUS.md](LEARNING_AND_PREDICTION_STATUS.md)  
**最終更新**: 2025-02-12

---

## 1. 現状の整理

### 1.1 精度指標の目標と現状（ドキュメント上の目安）

| 指標 | 目標 | 元の目安（改善前） | 備考 |
|------|------|---------------------|------|
| **的中率（3連単1位）** | 4.0% 以上 | 約 1.70% → 段階で 2.5%〜4% 想定 | 理論値 0.83% の約2倍からスタート |
| **報酬安定性（正の報酬率）** | 80% 以上 | 52.5% | 報酬設計で 70% 目標 |
| **平均報酬** | 30 以上 | 4.83 | 学習効率と連動 |
| **学習効率（理論比）** | 25 倍以上 | 16.2 倍 | ステップ数・評価エピソードで改善 |

※ 実際の数値は「学習 → 予測 → verify_predictions」のサイクルで計測する必要あり。

### 1.2 現在のパイプライン

- **学習**: `optimize_graduated_reward.py`（Optuna でハイパーパラメータ探索 + PPO 学習）  
  - 設定: `optimization_config.ini`（MODE=medium, TRIALS=20, YEAR_MONTH=2024-04 等）  
  - 高速/中/通常モードでステップ数・評価エピソードが変わる（[FAST_MODE_IMPLEMENTATION_SUMMARY.md](optimization/FAST_MODE_IMPLEMENTATION_SUMMARY.md)）
- **予測**: `prediction_tool.py` — **単一モデル**（`optuna_models/graduated_reward_best/best_model.zip`）で上位20組・購入提案を出力
- **検証**: `verify_predictions.py` — 予測JSON と race_data の着順を照合し、**1位/Top3/Top10/Top20 的中率・回収率**を算出

### 1.3 実装済みだが本番フローに未統合の機能

- **報酬設計の改善**（Phase 1）: 的中報酬強化・部分的中報酬化・ペナルティ緩和（`kyotei_env.py` 等）
- **学習時間延長**（Phase 2）: 20万ステップ・5000エピソード等（`optimize_graduated_reward.py`）
- **アンサンブル学習**: `tools/ensemble/ensemble_model.py` — 複数モデル・重み付き投票（**予測ツールからは未使用**）
- **継続的学習**: `tools/continuous/continuous_learning.py` — 既存モデル継承（**バッチ/本番フロー未接続**）
- **性能監視**: `tools/monitoring/performance_monitor.py` — 指標追跡・レポート（**定期実行・ダッシュボード未**）

---

## 2. やること一覧（優先度・フェーズ別）

### フェーズ A: 測定・検証の確立（最優先）

| # | やること | 内容 | 状態 |
|---|----------|------|------|
| A1 | **ベースライン計測** | 現在の best_model で「学習に使った月」と「未使用月」の両方について、`verify_predictions` で 1位/Top3/Top10/Top20 的中率・回収率を記録する。 | 未実施なら実施 |
| A2 | **検証の定期化** | 学習→予測を回すたびに `verify_predictions` を実行し、結果をログまたは CSV/JSON で残す（日付・データ範囲・モデル識別子付き）。 | 未 |
| A3 | **簡易ダッシュボード** | 的中率・回収率の時系列や「月別・会場別」の一覧を一画面で見られるようにする（スプレッドシート/ローカルHTML/モニタリングツールのいずれか）。 | 未 |

**成果**: 「何を変えたら精度がどう変わったか」を判断できる土台ができる。

---

### フェーズ B: 学習・最適化の強化

| # | やること | 内容 | 状態 |
|---|----------|------|------|
| B1 | **学習データ量の確保** | 学習に使う race_data + odds_data のペアを増やす（月・会場・日数を増やし、データ不足でスキップされるレースを減らす）。 | 要確認 |
| B2 | **Optuna 試行数・モードの見直し** | 精度優先なら MODE=normal・TRIALS=50 等で実行時間とトレードオフを検討。medium でベースラインを取り、normal で比較。 | 設定で対応可 |
| B3 | **ハイパーパラメータ範囲の再検討** | `optimize_graduated_reward.py` 内の learning_rate / batch_size / n_epochs 等の範囲を、既存ドキュメント（improvement_implementation_summary 等）と実測結果に合わせて調整。 | 随時 |
| B4 | **報酬パラメータの設定ファイル化** | 報酬の倍率・ペナルティを `improvement_config.json`（または ImprovementConfigManager）で変更できるようにし、コード変更なしで A/B 比較できるようにする。 | 一部済（要確認） |
| B5 | **学習ログと再現性** | 各実行の year-month / trials / mode / 報酬パラメータ / 使用データ件数をログに残し、どの設定で best_model ができたか追えるようにする。 | 一部済 |

**成果**: 同じデータで「設定だけ変えた比較」がしやすくなる。

---

### フェーズ C: モデル・予測の拡張

| # | やること | 内容 | 状態 |
|---|----------|------|------|
| C1 | **アンサンブル予測の接続** | 複数 best_model（別試行 or 別月学習）を `ensemble_model` で読み込み、`prediction_tool` からアンサンブル予測を出せるようにする。 | 未接続 |
| C2 | **予測ツールのモデル指定** | コマンドラインで「どの best_model（またはアンサンブル設定）を使うか」を指定できるようにする。 | 現状は固定パス |
| C3 | **継続学習のパイプライン化** | 既存 best_model を初期値にした継続学習を、`run_learning_prediction_cycle.bat` や月次バッチのオプションとして組み込む。 | 未 |
| C4 | **特徴量・状態ベクトルの見直し** | 現行の共通状態ベクトル（`get_state_dim() = 48 + 会場数 + 3`、オッズ非入力）に、会場・天候・調子・展示走情報等の追加特徴があるか検討し、あれば `state_vector.py` に組み込む（[trifecta_improvement_strategy](trifecta_improvement_strategy.md) の「統計的学習」「艇間相関」等を参照）。 | 要調査 |

**成果**: 単一モデル以上の精度・安定性を狙える。

---

### フェーズ D: 運用・監視

| # | やること | 内容 | 状態 |
|---|----------|------|------|
| D1 | **性能監視の定期実行** | `performance_monitor` を学習完了後に叩き、的中率・平均報酬・安定性を記録する。 | 未 |
| D2 | **アラート閾値** | 的中率が目標を下回った、または急落した場合にログ/メール等で通知する（閾値は config で指定）。 | 未 |
| D3 | **月次レポート** | 月ごとに「学習設定・使用データ・検証結果（的中率・回収率）」を1ファイルにまとめる。手動でも可、自動化できれば尚可。 | 未 |

**成果**: 精度の推移を追い、劣化に早く気づける。

---

## 3. すぐに着手しやすい項目（ショートリスト）

1. **A1**: いまの best_model で `verify_predictions` を複数日・複数月で実行し、ベースラインの数値をメモする。
2. **A2**: `run_learning_prediction_cycle.bat`（または同等フロー）の最後に `verify_predictions` を必ず実行し、結果を `logs/` に保存する。
3. **B2**: `optimization_config.ini` で MODE=normal, TRIALS=30〜50 を1回試し、medium との的中率・回収率を比較する。
4. **B4**: 報酬パラメータが `improvement_config.json` で切り替わっているか確認し、必要なら `optimize_graduated_reward` から読み込むようにする。
5. **C1**: 2〜3本の best_model（別 trial や別 year-month）を用意し、`EnsembleTrifectaModel` で予測 → 同じ日で `verify_predictions` し、単一モデルと比較する。

---

## 4. 参照ドキュメント

| ドキュメント | 内容 |
|--------------|------|
| [trifecta_improvement_strategy.md](trifecta_improvement_strategy.md) | 報酬設計・学習時間・アンサンブル・継続学習の優先度と方針 |
| [improvement_implementation_summary.md](improvement_implementation_summary.md) | Phase1〜4 の実装内容・期待効果・検証方法 |
| [LEARNING_AND_PREDICTION_STATUS.md](LEARNING_AND_PREDICTION_STATUS.md) | 学習・予測の実行手順とデータ前提 |
| [LEARNING_PREDICTION_CYCLE_IMPROVEMENTS.md](LEARNING_PREDICTION_CYCLE_IMPROVEMENTS.md) | 学習→予測サイクルの改善点と verify_predictions の使い方 |
| [config_usage_guide.md](config_usage_guide.md) | improvement_config のパラメータと変更方法 |
| [optimization/FAST_MODE_IMPLEMENTATION_SUMMARY.md](optimization/FAST_MODE_IMPLEMENTATION_SUMMARY.md) | モード別ステップ数・時間・精度トレードオフ |
| [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) | 性能・精度指標の概要と今後の展開 |

---

## 5. 進捗の更新のしかた

- 上表の「状態」を **未 / 着手 / 済** 等で更新する。
- 新しい施策（例: 新特徴量・新報酬設計）を試したら、表に行を追加し、対応する参照ドキュメントがあればリンクする。
- ベースラインや比較結果の数値は、このファイルの「現状の整理」セクションか、別の結果用 MD/CSV に追記するとよい。
