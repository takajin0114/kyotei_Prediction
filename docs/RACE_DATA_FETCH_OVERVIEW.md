# レースデータ取得処理 — 確認結果・詰めどころ

**目的**: レースデータ取得の処理を詰めるための現状整理。  
**確認日**: 2026-02-12

---

## 1. 処理の全体像

```
[データソース] boatrace.jp（公式）
       ↓
metaboatrace.scrapers (v1707) で HTML 取得・パース
       ↓
[単体] race_data_fetcher / odds_fetcher
[一括] batch_fetch_all_venues / retry_missing_races
[予測] prediction_tool / data_integration
       ↓
保存: kyotei_predictor/data/raw/YYYY-MM/ または outputs
```

---

## 2. 単体取得（1レース）

### 2.1 ファイル・関数一覧

| ファイル | 関数 | 取得内容 | レート制限 |
|----------|------|----------|------------|
| **race_data_fetcher.py** | `fetch_race_entry_data` | 出走表（選手・級別・勝率・艇・モーター・race_info） | 5秒 |
| **race_data_fetcher.py** | `fetch_race_result_data` | 結果（着順・ST・決まり手・天候・払戻） | 5秒 |
| **race_data_fetcher.py** | `fetch_complete_race_data` | 上記2つをマージ（entry + result） | 内側で各5秒 |
| **race_data_fetcher.py** | `fetch_before_information` | 直前情報（ST展示・周回展示・体重・艇設定・天候）※展示走後のみ | 5秒 |
| **odds_fetcher.py** | `fetch_trifecta_odds` | 3連単オッズ 120通り | 5秒 |

### 2.2 呼び出し元

| 呼び出し元 | 使用関数 | 用途 |
|------------|----------|------|
| batch_fetch_all_venues.py | fetch_complete_race_data, fetch_trifecta_odds | 過去一括取得（race + odds） |
| retry_missing_races.py | 同上 | 欠損レースの再取得 |
| prediction_tool.py | fetch_pre_race_data, fetch_trifecta_odds | 本番予測用（出走表＋直前情報＋オッズ） |
| data_integration.py | fetch_complete_race_data | Web のライブデータ取得 |
| app.py | fetch_race_entry_data | Web 用 |
| fast_future_entries_fetcher.py | fetch_race_entry_data | 出走表のみ先行取得 |
| scripts/verify_pre_race_fetch.py | fetch_race_entry_data, fetch_before_information, fetch_trifecta_odds | レース前取得の確認 |

### 2.3 詰めどころ（単体）

- **レート制限**: 現状 5秒/リクエスト。バッチでは 1秒に短縮しているが、単体・予測ツールは 5秒のまま。用途別に引数で指定できるようにするか検討。
- **エラー・リトライ**: race_data_fetcher 内の `safe_extract_*` は最大3回リトライ。選手名パース失敗時は「不明」で継続し成績・艇・モーターは保存。バッチ側でも max_retries=3。
- **レース中止**: `RaceCanceled` を raise。バッチでは `race_canceled_*.json` を書きスキップ。
- **直前情報**: 展示走前は空。予測パイプラインでは本番取得フローに組み込み済み（`fetch_pre_race_data`）。ただし現状の状態ベクトルには未組み込みで、追加特徴量候補として扱う。

---

## 3. 一括取得（バッチ）

### 3.1 batch_fetch_all_venues.py

- **入力**: `--start-date`, `--end-date`, `--stadiums`（カンマ or ALL）, `--schedule-workers`, `--race-workers`, `--is-child`
- **流れ**:
  1. 月間スケジュールで開催日・会場を取得（並列 8）
  2. 各 (日付, 会場, 1〜12R) で `fetch_race_data_parallel` を実行（並列 8、レート制限 1秒）
  3. `fetch_race_data_parallel` 内で: 既存ファイル・中止ファイルをスキップ → 無ければ `fetch_complete_race_data` → 成功なら race_data 保存 → `fetch_trifecta_odds` → odds 保存。中止時は `race_canceled_*.json` のみ作成。
- **保存先**: `kyotei_predictor/data/raw/YYYY-MM/`
  - `race_data_YYYY-MM-DD_会場名_R{n}.json`
  - `odds_data_YYYY-MM-DD_会場名_R{n}.json`
  - `race_canceled_YYYY-MM-DD_会場名_R{n}.json`
- **ログ出力先（統一）**: 標準出力に加え、**1日ごとに** `logs/batch_fetch_YYYY-MM-DD.log` に追記。日付が変わると翌日のファイルが新規作成される。共通モジュール `kyotei_predictor.utils.logger` の `get_daily_log_path("batch_fetch")` を使用。
- **多重起動防止**: `batch_fetch_all_venues.lock`

### 3.3 バッチの「止まり」検知（check_batch_fetch_stuck.sh）

長時間バッチを回すと、プロセスは生きているがログが更新されず実質ハングすることがある。以下で検知できる。

- **スクリプト**: `scripts/check_batch_fetch_stuck.sh`
- **検知条件**: (1) batch_fetch_all_venues 実行中 (2) 紐づくログの最終更新が N 分以上前 (3) Python 子プロセスの CPU 時間が数秒間増えていない → 止まっていると判断。
- **使い方**:
  - チェックのみ（止まっていたら exit 1）: `./scripts/check_batch_fetch_stuck.sh`
  - 止まっていたらプロセスを落とす: `./scripts/check_batch_fetch_stuck.sh --kill`
  - 閾値変更: `STALE_MINUTES=60 ./scripts/check_batch_fetch_stuck.sh`
- **定期実行例**（cron で 30 分ごと）:  
  `0,30 * * * * cd /path/to/kyotei_Prediction && ./scripts/check_batch_fetch_stuck.sh >> logs/check_stuck.log 2>&1`  
  止まったら自動で落としたい場合は `--kill` を付ける。

---

### 3.2 詰めどころ（バッチ）

- **レート制限**: 1秒固定。公式の利用規約・負荷を確認し、必要なら設定化（環境変数や ini）。
- **並列数**: schedule-workers=8, race-workers=8 がデフォルト。失敗増えたら下げる選択肢をドキュメント化。
- **リトライ**: レース取得・オッズ取得それぞれ max_retries=3。「データ未公開」はリトライ後にスキップし次回実行で再試行。
- **選手名解析エラー**: バッチ内で ValueError を捕捉し `log_racer_error` で JSONL 記録。race_data は entry 側で「不明」補完済みなら保存される想定だが、fetch_race_entry_data が None を返すケースの扱いを確認（現状はリトライして最終的に失敗なら race_success=False）。
- **retry_missing_races.py**: 既存の race/odds ペアで欠けているものを再取得。同じ fetch_complete_race_data / fetch_trifecta_odds を使用。日付範囲の指定方法を operations ドキュメントと揃える。

---

## 4. 予測フローでの取得

### 4.1 prediction_tool.py

- 指定日の開催会場を月間スケジュールで取得。
- 各会場・各レースで:
  - **レース前統合データ**: `fetch_pre_race_data`（出走表 + 取得できる場合は直前情報）
  - **オッズ**: `fetch_trifecta_odds`（締切後）
- 保存は prediction 結果（outputs/）。race_data / odds_data はメモリ上で使用し、raw には保存しない想定（必要ならオプションで保存を検討）。

### 4.2 詰めどころ（予測）

- **本番時刻**: 締切前はオッズ未公開のため、オッズ取得失敗を許容するか・リトライ時刻を分けるか検討。
- **直前情報**: 取得自体は `fetch_pre_race_data` で実施済み。使う場合は `build_race_state_vector` に特徴量を組み込む必要あり。
- **会場コード**: prediction_tool が StadiumTelCode をどう列挙しているか（全会場 or 指定会場）を確認。batch と同一マッピングか確認。

---

## 5. データ仕様・必須項目（再掲）

- **学習に必須**: race_info（日付・会場・レース番号・周回・進入固定）, race_entries（艇番・選手級別・勝率・艇・モーター）, race_records（着順）, odds_data（3連単 120通り）。
- **予測で状態生成に必須**: race_info + race_entries（状態はオッズ非依存）。
- **予測で期待値・購入提案に実質必須**: odds_data（未取得でも予測は継続できるが、期待値は暫定値になる）。
- **あるとよい**: weather_condition, start_time, total_time, winning_trick, payoffs。直前情報は追加特徴量候補。
- **取得元の詳細**: [RACE_DATA_ACQUISITION_AND_SOURCES.md](RACE_DATA_ACQUISITION_AND_SOURCES.md) 参照。

---

## 6. 詰める際のチェックリスト（案）

1. **レート制限**: 単体 5秒 / バッチ 1秒を設定ファイル or 環境変数で切り替え可能にする。
2. **ログ**: 取得成功/失敗・スキップ理由を共通フォーマット（例: 日付・会場・R番号・種別・結果・エラー種別）で出力し、バッチ・retry・予測で同じ形式に揃える。
3. **エラー分類**: ネットワークエラー / データ未公開 / レース中止 / 選手名パースエラー / その他 を区別し、リトライ可否・ログ・アラートを分ける。
4. **保存パス**: 常に `kyotei_predictor/data/raw/YYYY-MM/` に統一されているか確認。prediction_tool で raw に保存するオプションを足すか検討。
5. **直前情報**: 本番予測で使うか決め、使う場合は取得タイミング（展示走後）と特徴量組み込みを設計。
6. **テスト**: 単体（race_data_fetcher, odds_fetcher）のモックテストに加え、小範囲バッチ（1会場1日）で E2E 確認できる手順を docs/operations に明記。
7. **運用ドキュメント**: [operations/data_acquisition.md](operations/data_acquisition.md) と RACE_DATA_ACQUISITION_AND_SOURCES.md の実行例・トラブルシューティングを最新化。

---

## 7. 関連ファイル一覧

| 種別 | パス |
|------|------|
| 単体取得 | kyotei_predictor/tools/fetch/race_data_fetcher.py, odds_fetcher.py |
| 一括取得 | kyotei_predictor/tools/batch/batch_fetch_all_venues.py, retry_missing_races.py |
| 出走表のみ | kyotei_predictor/tools/batch/fast_future_entries_fetcher.py |
| 予測 | kyotei_predictor/tools/prediction_tool.py |
| Web・統合 | kyotei_predictor/data_integration.py, app.py |
| 確認用 | scripts/verify_pre_race_fetch.py |
| ドキュメント | docs/RACE_DATA_ACQUISITION_AND_SOURCES.md, docs/operations/data_acquisition.md, docs/PRE_RACE_FETCH_VERIFICATION.md |

---

**次のステップ**: 上記の「詰めどころ」「チェックリスト」から優先する項目を決め、該当ファイルを順に修正・テストするとよい。
