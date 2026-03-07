# State Vector 棚卸し：モーター・ボート情報

本ドキュメントでは、baseline B の学習入力である state vector において、モーター・ボート情報がどのように表現されているかを整理する。新特徴量をむやみに追加する前に、「今の構造で何が入っているか」を正確に把握することを目的とする。

---

## 1. 現在の State Vector 構造

### 1.1 全体次元数

| 構成 | 次元数 | 備考 |
|------|--------|------|
| 艇特徴 | 48 | 6艇 × 8次元/艇 |
| 会場 one-hot | len(stadium_names) | 通常 24 会場 |
| レース特徴 | 3 または 4 | race_num(1) + laps(1) + is_fixed(1) + motor_win_proxy(1, オプション) |
| **合計** | **48 + 会場数 + 3** または **+4** | motor_win_proxy はデフォルトOFF |

- **参照**: `kyotei_predictor/pipelines/state_vector.py` の `build_race_state_vector`, `get_state_dim`
- **データフロー**: `race_data` → `build_race_state_vector` → 1次元配列 → baseline B の入力

### 1.2 艇ごとの特徴量（1艇あたり 8 次元）

| 次元 | 名称 | 元データ | 値の種類 | 正規化 | 備考 |
|------|------|----------|----------|--------|------|
| 0 | pit | pit_number | 番号（枠番 1-6） | (pit-1)/5 | 艇番（枠）であり、boat_no/motor_no ではない |
| 1 | rating | racer.current_rating | 級別（A1/A2/B1/B2） | RATING_MAP → 1.0/0.75/0.5/0.25 | レーサー性能の代理 |
| 2 | perf_all | performance.rate_in_all_stadium | 性能値（全国勝率） | /10 | 0-1 付近 |
| 3 | perf_local | performance.rate_in_event_going_stadium | 性能値（当地勝率） | /10 | 0-1 付近 |
| 4 | boat2 | boat.quinella_rate | 性能値（ボート2連率 %） | /100 | 0-1 付近 |
| 5 | boat3 | boat.trio_rate | 性能値（ボート3連率 %） | /100 | 0-1 付近 |
| 6 | motor2 | motor.quinella_rate | 性能値（モーター2連率 %） | /100 | 0-1 付近 |
| 7 | motor3 | motor.trio_rate | 性能値（モーター3連率 %） | /100 | 0-1 付近 |

- **順序**: 艇 1〜6 の順に、各艇 8 次元ずつ並ぶ（先頭 8 次元 = 1号艇、次 8 次元 = 2号艇、…）。
- **欠損時**: boat/motor の quinella_rate, trio_rate が None の場合は 0 とする。

### 1.3 レース全体特徴量

| 次元 | 名称 | 元データ | 値の種類 | 備考 |
|------|------|----------|----------|------|
| - | venue_onehot | race_info.stadium | one-hot | 会場数分 |
| - | race_num | race_info.race_number | 番号 | (race_number-1)/11 で正規化 |
| - | laps | race_info.number_of_laps | 番号 | (laps-1)/4 で正規化 |
| - | is_fixed | race_info.is_course_fixed | フラグ | 0/1 |
| - | motor_win_proxy | オプション | 集約値 | 6艇の motor 2連率・3連率の平均。デフォルトOFF |

### 1.4 One-hot の有無

| 対象 | 有無 | 次元数 |
|------|------|--------|
| 会場 | あり | len(stadium_names) |
| 艇番（pit） | なし | pit は連続値 (pit-1)/5 で正規化 |
| 級別 | なし | RATING_MAP で 1 次元に圧縮 |
| ボート番号 | なし | 入っていない |
| モーター番号 | なし | 入っていない |

### 1.5 Motor / Boat に関係する列

| 種類 | 列 | 値の意味 | 備考 |
|------|-----|----------|------|
| 艇単位・性能値 | boat2 (各艇 5 番目) | ボート 2連率 | 艇ごとに個別 |
| 艇単位・性能値 | boat3 (各艇 6 番目) | ボート 3連率 | 艇ごとに個別 |
| 艇単位・性能値 | motor2 (各艇 7 番目) | モーター 2連率 | 艇ごとに個別 |
| 艇単位・性能値 | motor3 (各艇 8 番目) | モーター 3連率 | 艇ごとに個別 |
| レース単位・集約値 | motor_win_proxy (オプション) | 6艇の motor 2連率・3連率の平均 | デフォルトOFF |

---

## 2. モーター・ボート関連の分類

### 2.1 取得可能な元データ（race_data）

公式ページ・metaboatrace から取得可能な項目（`docs/RACE_DATA_ACQUISITION_AND_SOURCES.md` 参照）:

| 項目 | 取得可否 | 内容 |
|------|----------|------|
| boat.number | ✅ | ボート番号（艇の機材ID） |
| boat.quinella_rate | ✅ | ボート 2連率 |
| boat.trio_rate | ✅ | ボート 3連率 |
| motor.number | ✅ | モーター番号（機材ID） |
| motor.quinella_rate | ✅ | モーター 2連率 |
| motor.trio_rate | ✅ | モーター 3連率 |

- **単勝率**: 公式の出走表には単勝率は出ていない。2連率・3連率のみ取得可能（現状）。
- **ボート勝率・モーター勝率**: 単勝率が無いため、2連率・3連率を代理として利用している。

### 2.2 分類結果

| 観点 | 項目 | 現在の状態 |
|------|------|------------|
| **番号ベース** | motor_no | **入っていない**。motor.number は state vector に含めていない |
| **番号ベース** | boat_no | **入っていない**。boat.number は state vector に含めていない |
| **番号ベース** | pit_number | **入っている**。ただしこれは枠番（1-6）であり、boat_no / motor_no とは別物 |
| **性能値ベース** | motor 2連率・3連率 | **入っている**。艇ごとに motor2, motor3 として 2 次元 |
| **性能値ベース** | boat 2連率・3連率 | **入っている**。艇ごとに boat2, boat3 として 2 次元 |
| **集約値** | モーター勝率代理 | **部分的**。motor_win_proxy として 6艇平均を 1 次元。デフォルトOFF |
| **集約値** | ボート勝率代理 | **入っていない** |
| **艇ごとの個別値** | 各艇の motor2, motor3 | **入っている** |
| **艇ごとの個別値** | 各艇の boat2, boat3 | **入っている** |

### 2.3 判定サマリ

| 項目 | 判定 |
|------|------|
| motor_no, boat_no | 入っていない |
| motor 2連率・3連率（艇ごと） | 入っている |
| boat 2連率・3連率（艇ごと） | 入っている |
| motor 集約値（レース単位 1 次元） | 部分的（motor_win_proxy、デフォルトOFF） |
| boat 集約値 | 入っていない |
| 単勝率（motor / boat） | データに無いため、2連率・3連率を代理として利用 |

---

## 3. 「学習に効く形か」の評価

### 3.1 現状の良い点

1. **艇ごとの性能値が入っている**  
   各艇の boat 2連率・3連率、motor 2連率・3連率が、艇単位で独立した 4 次元として入っている。艇同士の差を表現できる。

2. **番号をそのまま使っていない**  
   motor_no, boat_no は含めていない。番号だけではモデルが扱いづらく、また同一機材の履歴を別途集計しない限り意味が薄いため、性能値（2連率・3連率）を直接使う設計は妥当。

3. **0-1 付近に正規化**  
   2連率・3連率は % を /100 しており、他の特徴量とスケールが揃っている。

4. **レーサー性能と分離**  
   perf_all, perf_local（選手）、boat2/boat3, motor2/motor3（艇・モーター）が分かれているため、役割が明確。

### 3.2 現状の問題点

1. **単勝率がない**  
   公式データには単勝率が無く、2連率・3連率を代理として使っている。単勝との相関はあるが完全一致ではない。

2. **motor_win_proxy が悪化した理由の候補**  
   - **集約で情報を潰しすぎ**: 6艇の平均を 1 次元にすると、艇ごとの差が消える。baseline B はすでに艇ごとの motor2, motor3 を持っているため、重複かつ劣化した情報になる可能性。
   - **過学習のリスク**: 学習データでの平均が、検証期間の分布とずれていると、汎化を悪化させる。
   - **既存特徴量との相関**: motor2, motor3 の平均と、各艇の motor2, motor3 が高い相関になりやすく、新たな情報量が少ない。

3. **boat の集約値は未検証**  
   motor_win_proxy を試したが boat 版は未実装。boat 集約を追加する効果は不明（仮説としては motor と同様に悪化する可能性もあり）。

4. **pit と boat_no / motor_no の混同**  
   pit は枠番（1-6）であり、boat.number / motor.number とは別。機材IDそのものは state vector に含んでおらず、意図的な設計である。

### 3.3 motor_win_proxy が悪化した理由の仮説（まとめ）

| 仮説 | 根拠 |
|------|------|
| 艇ごとの motor2, motor3 で十分で、集約は冗長 | 既に 6艇×2=12 次元で motor 情報があり、平均 1 次元は情報を圧縮しすぎ |
| 学習データへの過適合 | 6艇平均が train 期間に最適化され、test 期間で外れやすい |
| 相関の高い特徴量追加によるノイズ | 既存 motor 特徴と相関が高く、正則化や分割でむしろ不安定になった可能性 |

- **事実**: motor_win_proxy 追加後に rolling validation で全戦略が悪化（正のROI 0/4）。  
- **仮説**: 上記のいずれか、または組み合わせ。検証は今後の実験次第。

---

## 4. 今後の改善候補

### 4.1 追加不要とする理由

1. **艇ごとの motor / boat 性能値は既に入っている**  
   追加しなくても、motor2, motor3, boat2, boat3 で機材性能は表現されている。

2. **集約値（motor_win_proxy）は効果なし**  
   実験の結果、悪化した。同様の集約を boat で試しても、効果は不透明。

3. **番号（motor_no, boat_no）の追加**  
   機材IDをそのまま入れると、one-hot 化すると次元が増えすぎる。別途「機材ごとの成績テーブル」を作り、それを参照する形でないと学習に効きにくい。設計が複雑になる。

4. **calibration が有効**  
   特徴量追加よりも、既存特徴量の出力確率のキャリブレーション（sigmoid / isotonic）で rolling が改善している。まずはそちらを優先する方が妥当。

### 4.2 追加するなら有望な形

| 候補 | 内容 | 備考 |
|------|------|------|
| 艇ごとの boat 単勝率代理 | 2連率・3連率の加重平均など | データに単勝率が無いため、要検討 |
| 展示タイム・スタートタイミング | 別スコープ。今回は使わない | 不安定・取得タイミングの制約あり |
| calibration の継続 | 既存特徴量のまま確率補正 | 現時点で効果が出ている |

### 4.3 現時点での推奨方針

1. **新特徴量の追加は当面控える**  
   モーター・ボート情報は、艇ごとの motor2, motor3, boat2, boat3 で既にカバーされている。motor_win_proxy のような集約追加は効果がなく悪化した実績がある。

2. **calibration を主戦略とする**  
   sigmoid / isotonic のキャリブレーションで rolling が改善しているため、現状の state vector のままキャリブレーションを優先する。

3. **番号（motor_no, boat_no）の追加は見送り**  
   設計が複雑になり、既存の性能値で代替できる範囲と判断する。将来的に機材履歴 DB を整備するなら再検討の余地あり。

4. **boat 集約値の追加も見送り**  
   motor_win_proxy と同様のパターンで悪化する可能性が高く、優先度は低い。

---

## 5. 参照

- **State vector 実装**: `kyotei_predictor/pipelines/state_vector.py`
- **学習・予測での利用**: `kyotei_predictor/application/baseline_train_usecase.py`, `baseline_predict_usecase.py`
- **元データ構造**: `docs/RACE_DATA_ACQUISITION_AND_SOURCES.md`
- **B案改善履歴**: `docs/B_BASELINE_IMPROVEMENT.md`
- **キャリブレーション結果**: `docs/EV_STRATEGY_EXPERIMENT.md`, `docs/TIME_SERIES_VALIDATION.md`
