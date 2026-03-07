# B案ベースライン改善メモ

B案をすぐに改善するのではなく、まず改善余地を整理するためのドキュメント。

---

## 現在の B 案

- **モデル**: ベースライン分類器（sklearn RandomForest / LightGBM / XGBoost）
- **タスク**: 3連単 120 クラスの多クラス分類（状態ベクトル → クラススコア）
- **入力**: 既存の `build_race_state_vector` で得られる状態ベクトル
- **出力**: 各 3連単の probability / rank。既存 betting_selector / verify にそのまま接続可能

---

## State Vector 棚卸し（モーター・ボート）

- **詳細**: `docs/STATE_VECTOR_AUDIT_MOTOR_BOAT.md` を参照
- **要点**: 艇ごとに boat 2連率・3連率、motor 2連率・3連率は既に 4 次元ずつ入っている（性能値ベース）。motor_no / boat_no（番号）は入っていない。motor_win_proxy（集約値）は rolling で悪化したためデフォルトOFF。**追加しない方がよい**方針を推奨。

---

## 改善候補

### 1. 特徴量拡張

現在の状態ベクトルに足す候補。モーター・ボートについては上記棚卸しを参照。

| 候補 | 説明 |
|------|------|
| **モーター勝率** | モーターの連対率・3連対率（既存 boat/motor の拡張） |
| **ボート勝率** | ボートの連対率・3連対率 |
| **展示タイム** | 展示走のタイム・偏差。スタートの速さの指標 |
| **スタートタイミング** | 平均スタートタイミング・フライング/出遅れ回数（performance に一部あり） |
| **枠番補正** | 1号艇・2号艇等の枠番による有利不利の補正 |
| **級別・支部** | レーサーの級別・支部情報の効き方の見直し |
| **進入コース** | まわり脚・イン脚等の傾向（データがあれば） |

実装方針: `build_race_state_vector` の拡張または B案専用の特徴量パイプラインを infrastructure に追加し、既存 A案は触らない。

---

### 2. 順位確率モデル

3連単 120 クラスを直接予測するのではなく、1着・2着・3着を別モデルで予測する構造。

| 要素 | 説明 |
|------|------|
| **P(1着)** | 各艇の1着確率を予測するモデル（6クラス or 回帰） |
| **P(2着)** | 1着が決まった条件付きで2着確率（または2着専用モデル） |
| **P(3着)** | 1-2着が決まった条件付きで3着確率 |

3連単確率は、条件付き確率の積で近似する。

- 例: P(1-2-3) ≈ P(1着=1) × P(2着=2 | 1着=1) × P(3着=3 | 1着=1, 2着=2)
- メリット: 解釈しやすく、1着精度を優先した設計にしやすい
- デメリット: モデル数・学習パイプラインが増える

---

### 3. その他

- **学習データの期間・会場バランス**: 特定会場に偏らないようサンプリングする。
- **クラス不均衡**: 120 クラスの出現頻度に偏りがある場合は、重み付け学習やサンプリングの検討。
- **検証指標**: ROI に加え、ランキング相関（予測順位と実着順の一致度）なども見る。

---

## 進め方

1. A/B 実験で「B案がどこで外しているか」をレース別に確認する。
2. 外しの傾向（会場・枠番・展示タイム等）に合わせて、上記の特徴量拡張から優先度の高いものを1つ選び、最小限だけ追加する。
3. 順位確率モデルは、特徴量拡張である程度伸ばした後に検討する。

---

## 実施した改善（ロールング検証スプリント）

### 選んだ改善テーマ: 学習期間の拡張（候補C）

- **内容**: ロールング検証の各 window で、train を 15日 から **30日** に拡張する（test 開始日の最大30日前から train_end までを使用）。
- **選定理由**: モデル構造を変えず、既存の `collect_training_data` に日付フィルタ（`train_start` / `train_end`）を追加するだけで試せる。汎化には「より多くの過去データ」が有効という仮説を検証したかった。

### 実装

- `baseline_train_usecase.py`: `_parse_date_from_race_path` を追加し、`collect_training_data` および `run_baseline_train` に `train_start` / `train_end`（YYYY-MM-DD）を追加。ファイル名から日付を抽出し、指定範囲外のレースを学習から除外。
- `cli/baseline_train.py`: `--train-start` / `--train-end` オプションを追加。
- `tools/rolling_validation_windows.py`: 4 window × 改善前(15日)・改善後(30日) を実行し、戦略別に集計・before/after 比較を JSON で保存。

### 結果

- **改善前（15日学習）**: B top_n=5 EV>1.10 で平均 ROI +19.69%、4 window 中 2 つでプラス。EV>1.15 も同様に 2/4 プラス。
- **改善後（30日学習）**: 全戦略で平均 ROI がマイナスに（-40% 前後）。正の ROI を出した window は 0/4。
- **結論**: 今回のデータ・期間では **学習期間の拡張は汎化改善にならなかった**。短い window（15日）で直近に合わせて学習した方がロールング検証スコアは良かった。

### 今後の候補

1. **特徴量の1つ追加**（候補A）: モーター勝率・ボート勝率・展示タイムなど、既存 state_vector に1列だけ足して同様のロールング検証で効果を見る。
2. **確率の後処理**（候補B）: calibration や上位候補の再スコアリングで、EV 閾値の効き方を変える。
3. **学習データのバランス**: 会場・時期のサンプリング調整（偏りを減らす）。

---

## 実施した改善（特徴量1つ追加スプリント）

### 追加した特徴量: モーター勝率代理（候補A）

- **内容**: レース単位で「6艇の (motor.quinella_rate + motor.trio_rate) / 2 を 0–1 正規化した平均」を 1 次元スカラーとして状態ベクトル末尾に追加。単勝率がデータにないため 2連率・3連率の平均を代理とした。
- **選定理由**: モーター性能は結果に効きうるため、既存の boat/motor 情報を補強する最小限の追加として選んだ。1 次元のみで before/after の因果を切り出しやすくするため。
- **実装**: `state_vector.py` に `motor_win_proxy` を追加。**現時点ではデフォルトOFF**（`KYOTEI_USE_MOTOR_WIN_PROXY=1` で有効）。無効時は従来次元（+3）、有効時は +1 次元（合計 +4）。欠損時は 0.5（中立）。

### before/after 比較（15日学習・7日検証・4 window）

| 戦略 | Before 平均ROI | Before 正のROI window | After 平均ROI | After 正のROI window |
|------|----------------|------------------------|---------------|----------------------|
| B top_n=3 | -1.14% | 1/4 | -20.49% | 0/4 |
| B top_n=5 EV>1.10 | 19.69% | 2/4 | -36.84% | 0/4 |
| B top_n=5 EV>1.15 | 18.39% | 2/4 | -39.55% | 0/4 |

- **結論**: モーター勝率代理を追加すると **汎化性能は悪化**。全戦略で平均 ROI がマイナスに転じ、正の ROI window は 0/4。今回のデータ・期間ではこの 1 特徴追加は有効でなかった。
- **効果の有無**: **効果なし（悪化）**。従来モデル（特徴量追加なし）のまま、EV 1.10〜1.15 で運用する方がロールング検証スコアは良い。
- **保存先**: **logs/rolling_validation_feature_before_after.json**
- **再実行**: `PYTHONPATH=. python3 kyotei_predictor/tools/rolling_validation_feature.py`（プロジェクトルートで実行）。

### 次候補（特徴量スプリント時点）

1. **別の特徴量を 1 つだけ試す**: ボート勝率（候補B）・展示タイム（候補C）・スタートタイミング（候補D）。同じ 15日 rolling で before/after 比較。
2. ~~**モーター勝率代理を外す**~~: **実施済み**。デフォルトを `KYOTEI_USE_MOTOR_WIN_PROXY=0`（OFF）に戻した。ON にするには `=1` を設定。
3. **確率の後処理**: calibration や EV 閾値の微調整で、既存特徴量のままスコアの質を上げる。→ 次スプリントで実施。

---

## 実施した改善（確率キャリブレーションスプリント）

### モーター勝率代理のデフォルトOFF

- **内容**: `KYOTEI_USE_MOTOR_WIN_PROXY` のデフォルトを OFF 相当に変更。従来特徴量を基準とした比較とする。
- **実装**: `state_vector.py` の `_use_motor_win_proxy_feature()` で、環境変数未設定時は `"0"` を参照し、`== "1"` のときのみ True。比較用に ON へ切り替える手段は残している。
- **docs**: 現時点ではデフォルトOFFであることを本メモおよび `state_vector.py` の docstring に明記。

### 確率キャリブレーションの導入

- **背景**: 特徴量追加は有効でなかったため、既存特徴量のままモデル出力確率の歪みを補正する方針。EV 戦略は確率の質に依存する。
- **導入した calibration**: **none**（なし）・**sigmoid**（Platt scaling）・**isotonic**（Isotonic regression）。設定で切り替え可能（`--calibration none|sigmoid|isotonic`）。
- **選んだ理由**: 実装量が少なく安定しやすい sklearn の `CalibratedClassifierCV`（cv='prefit'）を利用。まず sigmoid を主に、isotonic も比較対象とした。
- **実装内容**:
  - 学習時: ベースモデル fit 後、`calibration in ("sigmoid","isotonic")` のとき `CalibratedClassifierCV(estimator=model, method=calib, cv="prefit").fit(X, y)` でキャリブレーションを fit（学習データのみ、test 期間は使わない）。
  - 予測時: 保存したモデル（キャリブレーション済みの場合はラッパー）の `predict_proba` をそのまま利用。
  - モデル保存・読込: `.meta.json` に `calibration` 種別を保存。予測結果の `model_info.calibration` に出力。
  - 変更箇所: `baseline_train_usecase.py`（calibration 引数・CalibratedClassifierCV 適用）、`baseline_model_repository.py`（メタデータに calibration）、`baseline_predict_usecase.py`（model_info に calibration）、`cli/baseline_train.py`（`--calibration`）、`rolling_validation_windows.run_one_window`（calibration 引数）。

### キャリブレーション比較結果（15日学習・7日検証・4 window）

| 戦略 | none 平均ROI | none 正のROI | sigmoid 平均ROI | sigmoid 正のROI | isotonic 平均ROI | isotonic 正のROI |
|------|--------------|--------------|-----------------|-----------------|------------------|------------------|
| B top_n=3 | -1.14% | 1/4 | 30.26% | 2/4 | 18.20% | 2/4 |
| B top_n=5 EV>1.10 | 19.69% | 2/4 | **53.54%** | 2/4 | **44.55%** | **3/4** |
| B top_n=5 EV>1.15 | 18.39% | 2/4 | **55.40%** | 2/4 | **40.51%** | 2/4 |

- **効果**: **キャリブレーション（sigmoid / isotonic）で汎化指標が改善**。sigmoid で平均 ROI が EV>1.10 で 19.69% → 53.54%、EV>1.15 で 18.39% → 55.40%。isotonic では EV>1.10 で 4 window 中 3 つが正の ROI。
- **結論**: 既存特徴量のまま確率キャリブレーションを導入することで、rolling validation 上の平均 ROI・中央値 ROI が向上。EV 1.10 / 1.15 の有効性は維持・強化されている。
- **保存先**: **logs/rolling_validation_calibration_before_after.json**, **logs/rolling_validation_calibration_compare.json**（同一内容・comparison_summary 付き）
- **再実行**: `PYTHONPATH=. python3 kyotei_predictor/tools/rolling_validation_calibration.py`

### 暫定推奨方式（rolling validation 比較の結論）

- **推奨**: **calibration=sigmoid**。平均 ROI が EV>1.10 で 53.54%、EV>1.15 で 55.40% と最も高い。
- **代替**: calibration=isotonic。EV>1.10 で正のROI window が 3/4 と安定する場合がある。平均 ROI は sigmoid より低いが、total_bet が少なめになる。
- **学習**: `--calibration sigmoid` で保存。予測は保存済みモデル（キャリブレーション込み）をそのまま利用する。

### 次候補（キャリブレーションスプリント後）

1. **本番推奨**: B案 + **calibration=sigmoid** + EV>1.10 または 1.15。rolling で平均 ROI が最大だった設定を暫定主戦略とする。
2. **キャリブレーションの微調整**: sigmoid と isotonic の併用や、閾値 1.05〜1.20 の細かい比較。
3. **学習データ・会場バランス**: 会場・時期のサンプリング調整で、さらに安定性を上げる。
