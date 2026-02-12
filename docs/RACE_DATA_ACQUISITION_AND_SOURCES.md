# レースデータ取得の処理とデータソース整理

**目的**: レースデータ取得処理の流れ、実際に参照しているサイト、取得できているデータ・必要なデータを洗い出す。  
**最終更新**: 2025-02-12

---

## 1. 参照しているサイト（データソース）

### 1.1 公式サイト（現行の取得元）

| 種別 | URL（実例・構造） | 用途 |
|------|-------------------|------|
| **出走表** | `https://boatrace.jp/owpc/pc/race/racelist?rno={レース番号}&jcd={会場2桁}&hd={YYYYMMDD}` | 出走表・選手・艇・モーター・成績 |
| **レース結果** | 結果ページ（metaboatrace の `result_page.location` で生成） | 着順・スタート展示・天候・払戻 |
| **3連単オッズ** | オッズページ（metaboatrace の `trifecta_page.location` で生成） | 3連単オッズ（120通り） |
| **直前情報** | `https://boatrace.jp/owpc/pc/race/beforeinfo?rno={レース番号}&jcd={会場2桁}&hd={YYYYMMDD}` | 展示走・スタート展示・選手コンディション・艇設定・天候（レース前・展示走実施後） |
| **月間スケジュール** | 月間スケジュールページ（`monthly_schedule_page.location`） | 開催日・会場の取得 |

- **ベースURL**: **https://boatrace.jp/**（BOAT RACE オフィシャルウェブサイト）
- **実装**: Python ライブラリ **metaboatrace.scrapers**（`requirements.txt` で `metaboatrace.scrapers==3.3.1`）の **v1707** 用スクレイパーを使用。  
  - 出走表: `metaboatrace.scrapers.official.website.v1707.pages.race.entry_page`  
  - 結果: `v1707.pages.race.result_page`  
  - 3連単オッズ: `v1707.pages.race.odds.trifecta_page`  
  - 直前情報: `v1707.pages.race.before_information_page`  
  - スケジュール: `v1707.pages.monthly_schedule_page`  
- **取得方法**: `requests.get(url)` で HTML を取得 → 各 scraping モジュールでパースし、構造化データに変換。

### 1.2 その他の公式データ（現行コードでは未使用）

| 種別 | URL・概要 | 備考 |
|------|------------|------|
| **一括ダウンロード** | https://www.boatrace.jp/owpc/pc/extra/data/download.html | 選手・成績・結果の CSV/LZH 等。別ツール（例: cstenmt/boatrace）で利用例あり。 |
| **アプリ用データ** | http://app.boatrace.jp/data/ 等 | BoatRaceDataCollector 等で利用例あり。 |

本プロジェクトでは **metaboatrace 経由の「出走表・結果・3連単オッズ・月間スケジュール」のみ**使用。

---

## 2. 取得処理の流れ（コード）

### 2.1 単体取得（1レース）

| 処理 | ファイル | 関数 | 内容 |
|------|----------|------|------|
| 出走表 | `tools/fetch/race_data_fetcher.py` | `fetch_race_entry_data(race_date, stadium_code, race_number)` | 出走表URL取得 → HTML パース → race_info / race_entries（選手・成績・艇・モーター）を返す |
| 結果 | 同上 | `fetch_race_result_data(...)` | 結果URL取得 → race_records / weather_condition / payoffs を返す |
| 統合 | 同上 | `fetch_complete_race_data(...)` | 上記2つを実行し `{ ...entry_data, ...result_data }` でマージ |
| 3連単オッズ | `tools/fetch/odds_fetcher.py` | `fetch_trifecta_odds(race_date, stadium_code, race_number)` | オッズURL取得 → 120通り分の combination / ratio を返す |
| 直前情報 | `tools/fetch/race_data_fetcher.py` | `fetch_before_information(race_date, stadium_code, race_number)` | 直前情報URL取得 → スタート展示・周回展示・選手コンディション・艇設定・天候（展示走実施後のみ取得可） |

- レート制限: 各リクエスト後に `time.sleep(5)`（race_data_fetcher）/ `time.sleep(5)`（odds_fetcher）。  
- バッチでは `batch_fetch_all_venues.py` 内で 1 秒間隔等に短縮可能。

### 2.2 一括取得（バッチ）

| 処理 | ファイル | 概要 |
|------|----------|------|
| 開催日取得 | `tools/batch/batch_fetch_all_venues.py` | `create_monthly_schedule_page_url(year, month)` で月間スケジュールを取得し、期間内の開催日・会場を列挙 |
| レース＋オッズ取得 | 同上 | 各 (日付, 会場, レース番号) で `fetch_complete_race_data` と `fetch_trifecta_odds` を実行 |
| 保存 | 同上 | 月ごとサブディレクトリ `kyotei_predictor/data/raw/YYYY-MM/` に  
  - `race_data_YYYY-MM-DD_会場名_R{レース番号}.json`  
  - `odds_data_YYYY-MM-DD_会場名_R{レース番号}.json`  
  として保存。レース中止時は `race_canceled_*.json` を書きスキップ。

---

## 3. 取得できているデータ（現在のJSON構造）

### 3.1 race_data_*.json（出走表＋結果の統合）

| 大項目 | キー | 取得可否 | 内容例 |
|--------|------|----------|--------|
| **race_info** | date, stadium, race_number, url, title, deadline_at, number_of_laps, is_course_fixed | ✅ 取得可 | 日付・会場・レース番号・周回・進入固定等 |
| **race_entries** | 各艇の pit_number, racer, performance, boat, motor | ✅ 取得可 | 下表の通り |
| **race_records** | pit_number, start_course, start_time, total_time, arrival, winning_trick | ✅ 取得可 | 着順・スタート展示・決まり手等 |
| **weather_condition** | weather, wind_velocity, wind_angle, air_temperature, water_temperature, wavelength | ✅ 取得可 | 天候・風・気温・水温・波 |
| **payoffs** | betting_method, betting_numbers, amount | ✅ 取得可 | 2連単/2連複/3連単/3連複の払戻金 |

**race_entries 内の詳細（1艇あたり）**

| キー | 取得可否 | 内容 |
|------|----------|------|
| pit_number | ✅ | 艇番 1〜6 |
| racer.name | ✅ | 選手名（姓 名） |
| racer.registration_number | ✅ | 登録番号 |
| racer.current_rating | ✅ | 級別（A1/A2/B1/B2） |
| racer.branch, born_prefecture, birth_date, height, gender | △ | 公式ページに無い場合は null |
| performance.rate_in_all_stadium | ✅ | 全国勝率 |
| performance.rate_in_event_going_stadium | ✅ | 当地勝率 |
| boat.number, quinella_rate, trio_rate | ✅ | 艇番・連対率・3連対率 |
| motor.number, quinella_rate, trio_rate | ✅ | モーター番号・連対率・3連対率 |

### 3.2 odds_data_*.json

| キー | 取得可否 | 内容 |
|------|----------|------|
| race_date, stadium, race_number | ✅ | 識別子 |
| odds_data | ✅ | 3連単 120 通り |
| odds_data[].betting_numbers | ✅ | [1着, 2着, 3着] の艇番 |
| odds_data[].ratio | ✅ | 倍率（オッズ） |
| odds_data[].combination | ✅ | "1-2-3" 形式の文字列 |

### 3.3 レース前で取得する情報（本番予測用）

**本番のレース予測**では、レース前に以下を取得する。

| 種別 | 関数・ファイル | 取得タイミング | 内容 |
|------|----------------|----------------|------|
| **出走表** | `fetch_race_entry_data` | 締切前〜当日 | 選手・級別・勝率・艇・モーター・race_info |
| **3連単オッズ** | `fetch_trifecta_odds` | 締切後 | 120通りのオッズ（締切時） |
| **直前情報** | `fetch_before_information` | **展示走実施後のみ** | スタート展示（ST）・周回展示（展示タイム）・選手体重・調整・艇設定（チルト・新ペラ）・天候 |

直前情報の JSON 構造（`fetch_before_information` の戻り値）:

| キー | 内容 |
|------|------|
| race_info | date, stadium, race_number, url |
| start_exhibition | [{ pit_number, start_course, start_time }]（スタート展示のST。フライングは負値、出遅れは 1.0） |
| circumference_exhibition | [{ pit_number, exhibition_time }]（周回展示の展示タイム） |
| racer_conditions | [{ racer_registration_number, weight, adjust }] |
| boat_settings | [{ pit_number, tilt, is_new_propeller, motor_parts_exchanges? }] |
| weather_condition | weather, wind_velocity, wind_angle, air_temperature, water_temperature, wavelength |

展示走がまだ実施されていない・ページが空の場合は `fetch_before_information` は空の配列や None を返す。予測パイプラインでは**出走表＋3連単オッズ**を必須とし、直前情報は**取得できた場合にのみ**追加特徴量として利用可能（現状の状態ベクトルには未組み込み）。

---

## 4. 学習・予測で「必要」としているデータ

### 4.1 必須（ないと動かない）

| データ | 使っている場所 | 用途 |
|--------|-----------------|------|
| race_records（arrival, pit_number） | kyotei_env, verify_predictions, trifecta_dependent_model | 正解ラベル（3連単着順）・報酬計算・検証 |
| race_entries（各艇の pit_number, racer.current_rating, performance, boat, motor） | kyotei_env.vectorize_race_state, data_preprocessor | 状態ベクトル（192次元）の元 |
| race_info（stadium, race_number, number_of_laps, is_course_fixed） | kyotei_env.vectorize_race_state | レース全体特徴・会場 one-hot |
| odds_data（betting_numbers, ratio） | kyotei_env, calc_trifecta_reward, prediction_tool | オッズ特徴・払戻計算 |

### 4.2 あるとよい（精度・分析用）

| データ | 現状 | 用途 |
|--------|------|------|
| weather_condition | ✅ **取得済み**（結果ページから race_data に保存） | 状態ベクトルや分析に未使用。追加特徴量にできる |
| race_records.start_time, total_time, winning_trick | ✅ **取得済み**（結果ページから race_data に保存） | スタートタイミング・決まり手分析に未使用 |
| payoffs | ✅ 取得可 | 3連単払戻は odds と整合確認に利用可能。学習では odds_data を主に使用 |
| racer.birth_date, height, branch | △  null になりうる | 選手属性として追加可能 |
| 2連単・2連複・3連複オッズ | **使用しない**（オッズ取得できないため） | — |

### 4.3 要確認・未取得（公式等にありそうなもの）

| データ | 備考 |
|--------|------|
| **進入コース別成績・コース別タイム** | 公式「レース場データ」ページ（stadium?jcd=）にコース別入着率等あり。metaboatrace の entry には含まれず。**要確認・未取得**。 |
| 選手の級別別成績・連対率等の細分化 | 出走表に載っている範囲で取得済み。さらに細かい履歴は一括DL等。 |
| 日付をまたぐ「直前Nレース」の調子 | 自作で race_data を蓄積して集計する必要あり。 |
| **オッズ変動履歴（時間軸）** | 公式は「締切時オッズ」のみ提供。複数時刻の取得は別途蓄積が必要。**未取得**。 |

---

## 5. 取得可否・必要性の一覧表（まとめ）

| データ項目 | 取得元（サイト/ページ） | 取得可否 | 学習/予測で必要か |
|------------|------------------------|----------|-------------------|
| 日付・会場・レース番号 | 出走表・結果・オッズ | ✅ | ✅ 必須 |
| 出走表（6艇の選手・級別・勝率・艇・モーター） | 出走表 | ✅ | ✅ 必須 |
| 着順・スタート展示・決まり手・タイム | 結果 | ✅ | 着順は必須、他は任意 |
| 天候・風・気温・水温・波（weather_condition） | 結果 | ✅ 取得済み | 任意（未使用） |
| 3連単オッズ（120通り） | 3連単オッズ（metaboatrace） | ✅ | ✅ 必須 |
| 2連単・2連複・3連複オッズ | — | **使用しない**（取得できないため） | — |
| 払戻（2連単/2連複/3連単/3連複） | 結果 | ✅ | 任意（検証用） |
| 月間スケジュール（開催日・会場） | 月間スケジュール | ✅ | ✅ バッチで使用 |
| 一括CSV/LZH（選手・成績・結果） | 公式ダウンロード | 別途取得可 | 現行は未使用 |
| 進入コース別成績・コース別タイム | 公式レース場データ等 | **要確認・未取得** | 任意 |
| オッズ変動履歴（時間軸） | 公式は締切時のみ | **未取得**（別途蓄積が必要） | 任意 |
| **直前情報**（スタート展示ST・展示タイム・選手体重・艇設定・天候） | 直前情報ページ（beforeinfo） | ✅ **取得可**（`fetch_before_information`。展示走実施後のみ） | 任意（追加特徴量候補） |

---

## 6. 推奨アクション（データ面）

1. **必須データ**: 現状の「出走表＋結果＋3連単オッズ」で必要な項目は一通り取得できている。  
   - 選手名のパース失敗時は `safe_extract_racers` でリトライ・スキップしているため、**成績・艇・モーター・級別**が取れていれば学習は可能。
2. **精度向上のため**:  
   - **weather_condition** を状態ベクトルや前処理に追加する（風・波・水温はコース有利不利に影響しうる）。  
   - **start_time / total_time / winning_trick** を学習後分析や特徴量に使うかを検討。  
   - **2連単・2連複・3連複オッズ**は取得できないため**使用しない**。
3. **運用**: 公式の **利用規約・アクセス頻度** を確認し、レート制限（現状 5 秒/1 秒）を守る。  
4. **公式一括DL**: 大量の過去データが必要な場合は、https://www.boatrace.jp/owpc/pc/extra/data/download.html の CSV/LZH と現行 JSON の役割分担を検討する。  
5. **進入コース別・オッズ変動**: 進入コース別は公式「レース場データ」ページ要確認。オッズ変動は締切時のみ取得のため、変動履歴は自前で複数時刻取得・蓄積が必要。  
6. **レース前情報**: 本番予測では**出走表＋3連単オッズ**で予測可能。**直前情報**（`fetch_before_information`）は展示走実施後に取得でき、スタート展示ST・展示タイム等を追加特徴量にできる（現状は未組み込み。必要に応じて `vectorize_race_state` 等で利用を検討）。

---

**参照コード**:  
- `kyotei_predictor/tools/fetch/race_data_fetcher.py`  
- `kyotei_predictor/tools/fetch/odds_fetcher.py`（3連単オッズのみ。2連単・2連複・3連複は使用しない）  
- `kyotei_predictor/tools/batch/batch_fetch_all_venues.py`  
- `kyotei_predictor/pipelines/kyotei_env.py`（vectorize_race_state, 報酬計算）
