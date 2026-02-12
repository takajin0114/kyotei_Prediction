# オッズの扱いと状態定義の共通化

**目的**: (1) オッズを「回収率計算専用」にする方針、(2) 学習と予測で状態定義を揃える方針をまとめる。  
**最終更新**: 2026-02-12

---

## 1. オッズは学習から除けてよいか

### 1.1 結論

**はい。オッズを状態（インプット）から除き、回収率計算だけに使う設計にしてよいです。**

- **学習**: 状態 = 出走表＋レース情報のみ（オッズなし）。報酬は「実際の着順」と「そのレースのオッズ」から計算する（払戻 = オッズ×賭け金）。つまり「どの組み合わせが勝つか」は状態から学習し、「どれだけ儲かるか」は報酬の大きさで反映される。
- **予測**: 状態 = 同じく出走表＋レース情報のみ。モデルは 3連単 120 通りの**確率**を出力。その後、**オッズは取得して回収率・期待値・購入提案の計算にだけ使う**。

これで「オッズはあくまで回収率計算のために使う」という運用に合います。

### 1.2 変更前と現行の役割

| 項目 | 変更前 | 現行 |
|------|------|--------------|
| **状態ベクトル** | 艇特徴 + レース特徴 + **オッズ120次元** | 艇特徴 + レース特徴のみ（オッズなし） |
| **報酬（学習時）** | 着順＋オッズで払戻を計算 | **同じ**（着順＋オッズで払戻を計算。オッズは「報酬計算用」としてファイルから読むだけ） |
| **予測時のオッズ** | 状態に含めて 192 次元を生成 | 状態には使わない。モデル出力（確率）を得たあと、別途オッズを取得し「期待値・回収率・購入提案」だけに使う |

### 1.3 実装で反映したポイント

- **学習**
  - `kyotei_env.py` の `vectorize_race_state` は `state_vector.build_race_state_vector(race, None)` を呼ぶ実装に統一。
  - `observation_space` は `shape=(get_state_dim(),)` に変更済み。
  - `KyoteiEnv.reset` では従来どおり odds ファイルを読み、`step` の報酬計算で使用（**報酬計算ではオッズを使う**）。
- **予測**
  - `vectorize_race_state_from_data` は `build_race_state_vector(race_data, None)` を利用。
  - 取得は `fetch_pre_race_data`（出走表 + 直前情報）を使用し、オッズは別取得して期待値・購入提案に利用。

オッズを状態から除いたことで、「出走表で確率推定」「オッズで期待値計算」の責務分離が明確になりました。

---

## 2. 学習と予測で状態の定義を共通化する（背景とメモ）

### 2.1 変更前にあったずれ（参考）

状態ベクトルを「どこで」「どう作っているか」が学習と予測で別実装になっており、次元や並びが一致していません。

| 項目 | 学習側（kyotei_env.py） | 予測側（prediction_tool.py） |
|------|-------------------------|------------------------------|
| **関数** | `vectorize_race_state(race_data_path, odds_data_path)` | `vectorize_race_state_from_data(race_data, odds_data)` |
| **会場 one-hot** | `stadiums = ['KIRYU','TODA','EDOGAWA']` の **3 会場** のみ | `stadiums[:9]` で **9 会場** |
| **会場の並び** | 上記 3 の固定リスト | 24 会場リストの先頭 9 つ（別順序の可能性） |
| **艇特徴** | 6×8=48。正規化・one-hot は同一ロジック | 同じ 48。ロジックは重複実装 |
| **レース特徴** | race_num, laps, is_fixed の 3 次元 | 同じ 3 次元 |
| **オッズ** | 120 次元（log+minmax）を結合 | 120 次元を結合し、さらに 12 次元パディング |
| **合計** | 48+6+120 = **174**（observation_space は 192 と宣言） | 48+12+120 = 180 → **192**（12 パディング） |

このため、変更前は学習時と予測時で「同じレース」を表すベクトルが異なり、モデル入力の解釈がぶれる可能性がありました。

### 2.2 共通化の目標（達成済み）

- **状態の定義は 1 箇所だけ**にする。学習も予測も、同じ関数（同じ特徴量の並び・同じ次元）を使う。
- **会場リストは 1 つ**に決め、one-hot の順序を固定する（`utils/venue_mapping` の `get_all_stadiums()` を使用）。
- **次元は固定**し、observation_space と実ベクトルの長さを一致させる。オッズを外す場合は「艇＋レースのみ」の固定次元にする。

### 2.3 共通化の実装手順（実施済み）

#### Step 1: 状態ベクトル生成を 1 モジュールに集約

- **置き場所の例**: `kyotei_predictor/pipelines/state_vector.py`（または `utils/state_vector.py`）。
- **提供する関数の例**:
  - `build_race_state_vector(race_data: dict, odds_data: dict | None = None) -> np.ndarray`
  - 引数 `odds_data` は互換用（現行は未使用）。
  - 戻り値は常に固定次元（`48 + 会場数 + 3`）。

#### Step 2: 会場リストの単一化

- **定義場所**: `utils/venue_mapping.py` の `VenueMapper.get_all_stadiums()` の順序を「状態ベクトル用の公式順」とする。
- **state_vector 側**: `VenueMapper.get_all_stadiums()` から会場名順を取得し、`会場数 + race_num + laps + is_fixed` を結合する。

#### Step 3: 特徴量の並びを明文化

- ドキュメントとコメントで、次の順で固定する:
  1. **艇特徴**: 艇1〜6 の順。各艇 8 次元: [艇番正規化, 級別スカラー, 全国勝率, 当地勝率, 艇連対率, 艇3連対率, モーター連対率, モーター3連対率]。
  2. **レース特徴**: 会場 one-hot(会場数), race_number 正規化(1), number_of_laps 正規化(1), is_course_fixed(1)。
- 合計: `48 + 会場数 + 3`（現行コードでは `get_state_dim()` で管理）。

#### Step 4: 学習側の差し替え

- `kyotei_env.py` の `vectorize_race_state`: 中身を `from kyotei_predictor.pipelines.state_vector import build_race_state_vector` を呼ぶだけにする。ファイルパスから race/odds を読み、dict にしたうえで `build_race_state_vector(race, odds)` を呼ぶ（オッズを除くなら `build_race_state_vector(race, None)` にして、報酬計算用のオッズは別途 reset で読み込んだ odds を保持して step で使う）。
- `observation_space`: `build_race_state_vector` の出力次元に合わせて `shape=(get_state_dim(),)` に変更。

#### Step 5: 予測側の差し替え

- `prediction_tool.py` の `vectorize_race_state_from_data`: 同じく `build_race_state_vector(race_data, odds_data or None)` を呼ぶだけにする。既存の重複ロジック（会場リスト・艇の正規化・オッズの minmax など）は削除。
- 予測時のレース前取得は `fetch_pre_race_data` に統一し、直前情報の受け皿を追加。

#### Step 6: 次元と互換性のテスト

- 学習用の race/odds のペアを 1 つ用意し、`build_race_state_vector(race, None)` と `build_race_state_vector(race, odds)` の両方で長さ・値の範囲を確認。
- 学習環境の `reset()` で得る observation の shape と、予測ツールで同じ race_data から作るベクトルの shape が一致することを単体テストで担保する。
- `kyotei_predictor/tests/test_state_vector.py` で共通状態ベクトルの基本テストを追加済み。

### 2.4 共通化後の状態スキーマ（例・オッズなし）

- **次元**: `48 + 会場数 + 3`（`get_state_dim()` で参照）。
- **並び**:
  - [0:48]   艇特徴 6×8
  - [48:]    レース特徴（会場 one-hot + race_num + laps + is_fixed）
- **オッズ**: 状態には含めない。回収率・期待値は予測後にオッズデータを使って別計算。

---

## 3. まとめ

| テーマ | 方針 |
|--------|------|
| **オッズの扱い** | オッズは学習の状態から除いてよい。報酬計算では従来どおりオッズを使い、回収率・期待値・購入提案は予測後にオッズを使って計算する。 |
| **状態の共通化** | 状態ベクトル生成を `state_vector.py` に集約し、会場リスト・特徴の並び・次元を学習と予測で同一化する。 |

今後の変更でも、まず `state_vector.py` を基準に定義を揃えたうえで、学習側・予測側へ反映する運用が安全です。
