# 特徴量・状態ベクトルの見直し（3.3.3 検討メモ）

**目的**: 学習と予測で同じ状態定義を使い、必要に応じて展示走・天候等の直前情報を状態に組み込むか検討する。  
**参照**: [state_vector.py](../kyotei_predictor/pipelines/state_vector.py)、[ODDS_AND_STATE_DESIGN.md](ODDS_AND_STATE_DESIGN.md)

---

## 現状

- **状態ベクトル**: `build_race_state_vector(race_data, odds_data)` で 1 レースあたり 1 本のベクトルを生成。オッズは状態に含めない（回収率・期待値は予測後に計算）。
- **艇あたり 8 次元**: pit(1) + rating(1) + rate_in_all_stadium, rate_in_event_going_stadium, boat_quinella_rate, motor_quinella_rate 等 6 次元。
- **レース特徴**: 会場 one-hot + レース番号 + 周回 + 決まり手フラグ等。会場リストは `VenueMapper.get_all_stadiums()` で取得。

---

## 検討項目

| 項目 | 内容 | メモ |
|------|------|------|
| **展示走** | 展示走の結果（タイム・進入など）を状態に含めるか | 取得元・形式が確定していれば 1 艇あたりの次元を増やす。学習データと予測時で同じ項目を用意する必要あり。 |
| **天候** | 天候・風向・波の情報を状態に含めるか | 現状 `weather_condition` 等が race_data にあっても state_vector では未使用。会場・日付で一意ならレース特徴に 1 ブロック追加可能。 |
| **直前情報** | 直前オッズ・出走表の更新を状態に含めるか | オッズは「状態に含めない」方針のため、直前オッズは状態には入れず予測後の期待値計算にのみ使う。出走表の更新（欠場など）は race_entries に反映されていれば現状の状態に含まれる。 |
| **同一定義** | 学習と予測で同じ `build_race_state_vector` を使う | すでに pipelines/state_vector を学習・予測の両方で参照している。新規特徴を追加する場合は両方のパスで同じ race_data 項目を参照するようにする。 |

---

## 追加する場合の手順

1. **データ取得**: 展示走・天候をどこから取得するか（既存 fetcher / 別 API）を決め、race_data または race_info にフィールドを追加する。
2. **state_vector.py**: `build_race_state_vector` 内でそのフィールドを読み、次元を拡張する。`get_state_dim()` の戻り値を合わせて更新する。
3. **学習**: KyoteiEnv が state を返す際に既に `build_race_state_vector` を使っているため、データに項目が入っていれば自動で反映される。
4. **予測**: prediction_tool の `vectorize_race_state_from_data` が同じ state_vector を使っているため、同上。

---

## 参照

- [LEARNING_INPUT_OUTPUT.md](LEARNING_INPUT_OUTPUT.md) — 学習のインプット（race_data の必須項目）
- [RACE_DATA_ACQUISITION_AND_SOURCES.md](RACE_DATA_ACQUISITION_AND_SOURCES.md) — 取得可能なデータ一覧
