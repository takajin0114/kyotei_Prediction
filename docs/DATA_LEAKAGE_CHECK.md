# 最終オッズリーク確認

学習・予測の特徴量に「最終オッズ」やレース終了後でないと分からない情報が混入していないかを確認した結果です。

---

## 確認対象

- baseline B の学習データ生成（`baseline_train_usecase.collect_training_data`）
- 特徴量生成（`pipelines/state_vector.build_race_state_vector`）
- 学習・予測で使う特徴量（列）の出所
- compare_ab / baseline_train_usecase / baseline_predict_usecase の入力
- config や feature selection に odds 系列が入っていないか

---

## 実際に学習・予測に使われている列（状態ベクトル）

baseline B は **1本の状態ベクトル**のみを使用。列名付きの DataFrame は使っておらず、`build_race_state_vector(race_data, None)` の戻り値（float 配列）をそのまま学習・予測に渡している。

### 状態ベクトルの構成（state_vector.py）

| 区分 | 内容 | 次元 | 出所 |
|------|------|------|------|
| 艇特徴 | 6艇 × 8次元 | 48 | race_entries[].pit_number, racer.current_rating, performance.(rate_in_all_stadium, rate_in_event_going_stadium), boat.(quinella_rate, trio_rate), motor.(quinella_rate, trio_rate) |
| レース特徴 | 会場 one-hot | len(stadium_names) | race_info.stadium |
| レース特徴 | レース番号・周回・コース固定 | 3 | race_info.race_number, number_of_laps, is_course_fixed |

- **オッズ**: 状態ベクトルには含めていない。docstring で「オッズは状態に含めず」と明記し、`odds_data` は引数で受け取るが未使用（互換用）。
- **race_records（着順）**: 正解ラベル（3連単クラス）の取得にのみ使用。特徴量には使っていない。

---

## リークの疑いがある列

- **odds / final_odds / payout / popularity_rank / 単勝オッズ相当**: 状態ベクトルには存在しない。**疑いなし。**
- **レース終了後でないと分からない列**: 状態ベクトルは race_info と race_entries のみから構成され、race_records はラベル用のみ。**疑いなし。**

---

## 判定

**安全**

- 学習: `race_data_*.json` のみ読み、`build_race_state_vector(race_data, None)` で特徴量を生成。オッズファイルは読んでいない。
- 予測: 同様に `build_race_state_vector(race_data, None)` のみでモデル入力を作成。オッズは **予測後** に `_attach_odds_to_combinations` で all_combinations に付与し、EV 選定・検証で使用している（買い目選定と ROI 計算用であり、特徴量ではない）。

---

## 運用ルール（今後の運用）

| フェーズ | オッズの扱い |
|----------|--------------|
| **学習** | 最終オッズを特徴量に使わない。出走表・レース情報のみで状態ベクトルを構成する。 |
| **検証（バックテスト）** | 確定後のオッズ（final odds）を EV 計算・払戻計算に使ってよい。 |
| **未来予測（本番）** | レース前のオッズ（current odds）のみ使用可能。本番では current odds で EV を計算し買い目を選ぶ。 |

---

## 要修正の有無

**要修正なし。** 現状の実装で最終オッズのリークはない。

---

## 参照コード

- 特徴量: `kyotei_predictor/pipelines/state_vector.py` の `build_race_state_vector`
- 学習: `kyotei_predictor/application/baseline_train_usecase.py` の `collect_training_data`（`build_race_state_vector(race_data, None)` のみ使用）
- 予測: `kyotei_predictor/application/baseline_predict_usecase.py`（状態は同上。オッズは `_attach_odds_to_combinations` で予測結果に付与）
- オッズ無視の単体テスト: `tests/test_state_vector.py` の `test_build_race_state_vector_ignores_odds`
