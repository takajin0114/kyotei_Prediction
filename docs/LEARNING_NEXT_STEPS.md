# 学習において次にやること

**役割**: 学習の評価・検証、ステップ数延長、Optuna、運用など「学習まわり」の次タスク。  
**索引**: [docs/README.md](README.md)（「タスク・次にやること」セクション）

**目的**: 強化学習（PPO・段階的報酬）の「次にやるべきこと」を優先度・フェーズ別に整理する。  
**参照**: [LEARNING_AND_PREDICTION_STATUS.md](LEARNING_AND_PREDICTION_STATUS.md), [PREDICTION_ACCURACY_IMPROVEMENT_TODO.md](PREDICTION_ACCURACY_IMPROVEMENT_TODO.md), [DATA_STORAGE_AND_DB.md](DATA_STORAGE_AND_DB.md)  
**最終更新**: 2026-03

---

## 直近の学習結果（2025年データ）

| 項目 | 値 |
|------|-----|
| **実行日時** | 2026-03-05 21:22:50 ～ 21:37:03 |
| **所要時間** | 約 14 分（852 秒） |
| **データ** | DB（2025-01-01 ～ 2025-12-31）、54,382 ペア |
| **総ステップ数** | 500,000 |
| **最終評価** | 平均報酬 = 22.98 ± 461.69 |
| **保存モデル** | `optuna_models/graduated_reward_final_20260305_213703.zip` |

※ 報酬のばらつき（±461.69）が大きいため、収束の確認やステップ数・ハイパーパラメータの見直しが有効。

---

## 1. 即時：評価・検証の確立（最優先）

「今のモデルでどこまで当たるか」を数値で押さえる。

| # | やること | 内容 |
|---|----------|------|
| **1.1** | **ベースライン計測** | 直近の学習モデル（`graduated_reward_final_*.zip` または `best_model.zip`）で予測を実行し、`verify_predictions` で **1位 / Top3 / Top10 / Top20 の的中率・回収率** を記録する。学習に使っていない月のデータでも検証するとよい。 |
| **1.2** | **best_model の更新** | 今回の `graduated_reward_final_20260305_213703.zip` が良ければ、`optuna_models/graduated_reward_best/best_model.zip` にコピーし、予測ツールから使えるようにする。 |
| **1.3** | **検証の習慣化** | 学習を回すたびに「予測 → verify_predictions」を実行し、結果をログまたは CSV/JSON に残す（日付・データ範囲・モデル識別子付き）。 |

**成果**: 「設定を変えたときに精度がどう変わったか」を判断できる土台ができる。

---

## 2. 短期：学習の改善

直近の 50 万ステップ・約 14 分をベースに、次のいずれかまたは複数を検討する。

| # | やること | 内容 |
|---|----------|------|
| **2.1** | **ステップ数の延長** | `train_with_graduated_reward` の `--total-timesteps` を 100 万〜200 万に増やして再学習し、評価報酬・検証結果を比較する。 |
| **2.2** | **Optuna でハイパーパラメータ探索** | 固定パラメータの代わりに `optimize_graduated_reward.py` を使い、`--data-source db --date-from 2025-01-01 --date-to 2025-12-31` で 2025 年データを指定。`--n-trials` を 20〜50 にし、最良トライアルのモデルを best として保存する。 |
| **2.3** | **報酬・ハイパーパラメータの確認** | `kyotei_env.py` の報酬設計（的中倍率・部分的中・ペナルティ）と、`improvement_config.json` / ImprovementConfigManager の連携を確認。必要ならパラメータを設定ファイルで切り替えられるようにする。 |
| **2.4** | **学習ログの記録** | 各実行で「データ範囲・総ステップ数・使用ペア数・最終評価報酬・保存モデルパス」を 1 行〜短いログに残し、再現性を確保する。 |

**成果**: 同じ 2025 年データで「ステップ数や Optuna の有無でどう変わるか」を比較できる。

---

## 3. 中期：パイプライン・運用

| # | やること | 内容 |
|---|----------|------|
| **3.1** | **学習データ量の確保** | 2026 年データの追加取得・DB 投入を行い、学習に使うペア数を維持・増やす。 |

**3.1.1 手順（2026年データを追加する場合）**: (1) バッチ取得で 2026 年を取得 → `data/raw/2026-MM/` に JSON 保存。(2) `import_raw_to_db` で DB に投入（[DATA_STORAGE_AND_DB.md](DATA_STORAGE_AND_DB.md) のコマンド例参照）。(3) 学習で `--date-from 2026-01-01 --date-to 2026-12-31` を指定して利用。

| **3.2** | **継続学習の利用** | 既存の best_model を初期値にした継続学習（`continuous_learning`）を、月次バッチや手動スクリプトのオプションとして組み込む。 |

**3.1.2 継続学習の実行例**: `kyotei_predictor.tools.continuous.continuous_learning` の `ContinuousLearningSystem` を使う。best_model を読み込み、新しいデータで追加学習する。

```python
from kyotei_predictor.tools.continuous.continuous_learning import create_continuous_learning_from_best_model

cls = create_continuous_learning_from_best_model("optuna_models/graduated_reward_best/best_model.zip")
cls.load_best_model()
cls.continue_learning(new_data_dir="kyotei_predictor/data/raw", additional_steps=50000)
# 保存は別途 model.save("path.zip") 等
```

バッチや run_learning_prediction_cycle から呼ぶ場合は、上記をスクリプト化するか、既存の `python kyotei_predictor/tools/continuous/continuous_learning.py` の利用を検討する（[improvement_implementation_summary.md](improvement_implementation_summary.md) 参照）。

| **3.3** | **アンサンブル予測の接続** | 複数モデル（別トライアル or 別年月）を `ensemble_model` で読み込み、`prediction_tool` からアンサンブル予測を出せるようにする。 |

**3.1.3 接続の現状と手順**: `EnsembleTrifectaModel`（`tools/ensemble/ensemble_model.py`）は複数 PPO の重み付き投票で action を返す。現状 `prediction_tool` は単一 `PPO` のみを `model` に持つ。接続するには、(1) prediction_tool が「単一 PPO または EnsembleTrifectaModel」のどちらでも受け付けるようにする、(2) 状態ベクトルを各モデルに渡し、確率（または action）を集約して 120 通りに変換する、という拡張が必要。実装時は `PredictionTool.__init__(model_path=...)` で複数パスを指定した場合に EnsembleTrifectaModel を組み立て、`predict_trifecta_probabilities_from_data` 内で ensemble.predict(state) を使う分岐を追加する。

| **3.4** | **性能監視の定期実行** | 学習完了後に `performance_monitor` を実行し、的中率・平均報酬・安定性を記録する。 |

**性能監視の実行例**（学習・検証サイクルのあとに推奨）:

```bash
python -m kyotei_predictor.tools.monitoring.performance_monitor
```

評価結果（eval_results）を渡してメトリクスを追跡する場合は、スクリプト内で `PerformanceMonitor` を利用する。出力は `kyotei_predictor/monitoring` に保存される。

**成果**: 単一モデル以上の安定性・精度と、運用の見える化ができる。

---

## 4. 実行例のまとめ

### 直接訓練（今回と同じ 2025 年・DB）

```bash
# 50 万ステップ（デフォルト）
python -m kyotei_predictor.tools.batch.train_with_graduated_reward \
  --data-source db --date-from 2025-01-01 --date-to 2025-12-31

# 100 万ステップに延長（2.1.1 ステップ数延長）
python -m kyotei_predictor.tools.batch.train_with_graduated_reward \
  --data-source db --date-from 2025-01-01 --date-to 2025-12-31 --total-timesteps 1000000
```

**2.1.1 比較の記録**: 延長して再学習したら、同じ条件で予測 → `verify_predictions` を実行し、的中率・回収率を 50 万ステップ時と比較する。結果は `docs/monthly_reports/YYYY-MM.md` または `logs/` に残す。

### Optuna 最適化（DB・2025 年）（2.1.2）

```bash
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
  --data-source db --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --date-from 2025-01-01 --date-to 2025-12-31 \
  --n-trials 20
```

本番では `--n-trials` を 20〜50 にするとよい。最良トライアルのモデルはスクリプトが保存するので、良ければ `optuna_models/graduated_reward_best/best_model.zip` にコピーして予測ツールから利用する。

### 予測 → 検証（ベースライン計測）

```bash
# 予測（best_model または指定モデルで）
python -m kyotei_predictor.tools.prediction_tool --predict-date 2025-06-15 --data-dir kyotei_predictor/data/raw

# 検証（的中率・回収率）
python -m kyotei_predictor.tools.verify_predictions \
  --prediction outputs/predictions_2025-06-15.json \
  --data-dir kyotei_predictor/data/raw
```

---

## 5. チェックリスト（進めたら ✓）

- [ ] 1.1 直近モデルで verify_predictions を実行しベースラインを記録
- [ ] 1.2 必要なら best_model.zip を更新
- [ ] 1.3 学習実行のたびに検証結果をログに残す運用にする
- [ ] 2.1 総ステップ数を延長して再学習・比較
- [ ] 2.2 Optuna で 2025 年データを最適化し best を更新
- [ ] 2.3 報酬パラメータの設定ファイル化・確認
- [ ] 2.4 学習ログ（データ範囲・ステップ数・報酬・モデルパス）の記録
- [ ] 3.1 以降 必要に応じてデータ追加・継続学習・アンサンブル・監視を導入

---

## 6. 参照ドキュメント

| ドキュメント | 内容 |
|--------------|------|
| [LEARNING_AND_PREDICTION_STATUS.md](LEARNING_AND_PREDICTION_STATUS.md) | 学習・予測の実行手順とデータ前提 |
| [PREDICTION_ACCURACY_IMPROVEMENT_TODO.md](PREDICTION_ACCURACY_IMPROVEMENT_TODO.md) | 精度向上のフェーズ別タスク（測定・学習・モデル・運用） |
| [DATA_STORAGE_AND_DB.md](DATA_STORAGE_AND_DB.md) | データソース（file / db）と各処理の対応 |
| [RUN_VERIFICATION.md](RUN_VERIFICATION.md) | 実行確認の手順（venv・テスト・短い学習） |
| [trifecta_improvement_strategy.md](trifecta_improvement_strategy.md) | 報酬設計・学習時間・アンサンブルの方針 |
