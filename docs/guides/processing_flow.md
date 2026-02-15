# 処理の流れ（運用フロー）

ローカル PC またはスマホから Cursor にアクセスしてデータ取得・保管を行い、学習は Colab で行う運用を整理したものです。

---

## 全体の流れ（3フェーズ）

```
┌─────────────────────────────────────────────────────────────────────────┐
│ フェーズ1: ローカル or スマホ → Cursor                                   │
│   ・サイトからデータ取得                                                  │
│   ・取得データを保管（Google Drive 等）                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ フェーズ2: Colab                                                         │
│   ・保管したデータで学習                                                  │
│   ・モデル・結果を Drive に保存                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ フェーズ3: ローカル or スマホ → Cursor                                   │
│   ・サイトからデータ取得（予測用の最新データ）                             │
│   ・予測実行                                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## フェーズ1: データ取得と保管（Cursor）

**どこで**: ローカル PC またはスマホから **Cursor** にアクセス  
**やること**: サイトからデータを取得し、保管用の場所に保存する。

### 1-0. まず 1R だけ取得して疎通確認（推奨）

日本語パス（マイドライブ等）の環境でも実行できるよう、**スクリプトの場所を基準に動く**バッチを用意しています。

- **エクスプローラーでダブルクリック**: `scripts\fetch_one_race.bat`
- **PowerShell**: プロジェクトルートで `.\scripts\fetch_one_race.ps1`

1会場（桐生）・1日（2026-02-14）・**1R のみ**取得し、`kyotei_predictor/data/raw/2026-02/20260214/KIRYU/` に `race_data_*_R1.json` と `odds_data_*_R1.json` が出力されれば成功です。続けて、既存データの期間を指定して再取得します。

### 1-1. 取得データを Google Drive に直接保存する場合

（Drive がマウントされている環境、または Colab で一時実行する場合）

```bash
python -m kyotei_predictor.tools.batch.batch_fetch_all_venues \
  --start-date 2026-02-01 \
  --end-date 2026-02-14 \
  --stadiums ALL \
  --output-data-dir "/path/to/GoogleDrive/kyotei_prediction/data/raw"
```

- Windows で Drive をマウントしている場合は、上記の `/path/to/GoogleDrive` を実際のドライブパス（例: `G:/マイドライブ`）に置き換える。
- Colab のノートブックから実行する場合は `--output-data-dir "/content/drive/MyDrive/kyotei_prediction/data/raw"` のように指定する。

### 1-2. いったんローカルに保存し、あとで Drive に同期する場合

```bash
# 1) ローカルに取得
python -m kyotei_predictor.tools.batch.batch_fetch_all_venues \
  --start-date 2026-02-01 \
  --end-date 2026-02-14 \
  --stadiums ALL \
  --output-data-dir "kyotei_predictor/data/raw"

# 2) Drive へ同期（Drive がマウントされている場合）
python -m kyotei_predictor.tools.storage.drive_data_sync \
  --direction push \
  --local-dir kyotei_predictor/data/raw \
  --drive-dir "/path/to/GoogleDrive/kyotei_prediction/data/raw"
```

**保管先**: 上記のいずれかで **Google Drive** の `kyotei_prediction/data/raw` に取得データを置く。Colab はここを参照する。

### 1-3. 過去分のデータを取り直す（再取得）

**方法A: バッチを編集して実行（推奨）**

1. `scripts/fetch_reperiod.bat` を開く。
2. 次の変数を編集する。
   - `START_DATE` / `END_DATE` … 取り直したい期間（例: 2025-07-01 〜 2025-07-31）
   - `STADIUMS` … 会場（`ALL` または `KIRYU,EDOGAWA` などカンマ区切り）
   - `OUT_DIR` … 出力先（ローカルなら `kyotei_predictor/data/raw`、Drive ならそのパス）
   - `OVERWRITE=1` … **既存ファイルも上書きして取り直す**（過去分の取り直し時は 1 のまま）
3. バッチをダブルクリック、またはプロジェクトルートで `scripts\fetch_reperiod.bat` を実行。

**方法B: コマンドで直接実行**

```bash
# 過去分を取り直す（--overwrite で既存ファイルも上書き）
python -m kyotei_predictor.tools.batch.batch_fetch_all_venues ^
  --start-date 2025-07-01 ^
  --end-date 2025-07-31 ^
  --stadiums ALL ^
  --output-data-dir "kyotei_predictor/data/raw" ^
  --overwrite
```

- `--overwrite` を**付けない**場合: 既存のレース/オッズファイルはスキップされ、欠けている分だけ取得される。
- `--overwrite` を**付ける**場合: 指定期間の既存ファイルも上書きして再取得する（過去分の取り直し向け）。

再取得後、Drive に置く場合は 1-2 の同期（push）を実行するか、`--output-data-dir` に Drive のパスを指定して取得してください。

---

## フェーズ2: 保管データで学習（Colab）

**どこで**: **Google Colab**  
**やること**: Drive に保管したデータを使って学習し、モデル・結果を Drive に保存する。

1. Colab で Drive をマウントする。
2. リポジトリを clone し、`pip install -r requirements.txt` する。
3. 次のいずれかのノートブックを上から順に実行する。
   - `colab_drive_learning_cycle_template.ipynb`
   - `colab_drive_learning_cycle_gpu_template.ipynb`（GPU を使う場合）

ノートブック内で以下を指定する。

- **DRIVE_ROOT**: `'/content/drive/MyDrive/kyotei_prediction'`（保管先と同じルート）
- **DATA_DIR**: `f'{DRIVE_ROOT}/data/raw'`（フェーズ1で保存した取得データ）
- **YEAR_MONTH**, **PREDICT_DATE**, **N_TRIALS** などは任意で変更

実行すると、Drive 上の `data/raw` を読んで学習し、`optuna_models/`・`optuna_results/`・`outputs/` などを同じ Drive ルートへ保存する。

詳細: [Google Drive保存 + Colab学習ワークフロー](google_drive_colab_workflow.md)

---

## フェーズ3: データ取得と予測実行（Cursor）

**どこで**: 再度、ローカル PC またはスマホから **Cursor** にアクセス  
**やること**: 予測に必要な最新データをサイトから取得し、予測を実行する。

### 3-1. 予測用のデータを取得

```bash
# 予測対象日を含む期間で取得（例: 2026-02-14 を予測する場合）
python -m kyotei_predictor.tools.batch.batch_fetch_all_venues \
  --start-date 2026-02-14 \
  --end-date 2026-02-14 \
  --stadiums ALL \
  --output-data-dir "kyotei_predictor/data/raw"
```

- 保管先が Drive の場合は、`--output-data-dir` に Drive 上のパスを指定する（フェーズ1と同様）。

### 3-2. 予測実行

```bash
python -m kyotei_predictor.tools.prediction_tool \
  --predict-date 2026-02-14 \
  --data-dir "kyotei_predictor/data/raw"
```

- 学習済みモデルは Colab で Drive に保存しているため、ローカルで予測する場合は **Drive から `optuna_models/` をローカルにコピー**するか、予測ツールが参照する `optuna_models` のパスを Drive の場所に合わせて設定する必要がある。
- 予測も Colab で行う場合は、フェーズ2のノートブックで `--predict-date` を指定して実行すれば、Drive 上のデータ・モデルでそのまま予測される。

---

## 運用のまとめ

| フェーズ | 実施場所       | 主な作業                         | データの流れ |
|----------|----------------|----------------------------------|--------------|
| 1        | Cursor（端末） | サイトから取得 → 保管             | 取得データ → Drive |
| 2        | Colab          | 保管データで学習 → 成果物を保存   | Drive → 学習 → Drive |
| 3        | Cursor（端末） | サイトから取得 → 予測実行         | 取得データ + モデル → 予測結果 |

- **取得・保管**: Cursor（ローカル or スマホ）で実施し、保存先は **Google Drive** に統一すると、Colab と共有しやすい。
- **学習**: Colab のみ。Drive のデータを読んで学習し、モデルも Drive に保存する。
- **予測**: Cursor で実施する場合は、予測用データの取得と予測実行の両方を行う。モデルは Drive から取得するか、Colab 側で予測まで実行する運用でもよい。

---

## 関連ドキュメント

- [Google Drive保存 + Colab学習ワークフロー](google_drive_colab_workflow.md)
- [データ取得運用ガイド](../operations/data_acquisition.md)
- [バッチの使い方](batch_usage.md)
