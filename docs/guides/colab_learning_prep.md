# Colab 学習の準備チェックリスト

データ取得（バッチ）の待ち時間に、Colab での学習準備を進めるための手順です。

---

## 1. 今すぐできる準備（データ取得完了前）

### 1-1. Drive のフォルダ構成を用意

Google Drive の「マイドライブ」直下に、次のフォルダを作っておく（Colab から同じパスで参照するため）。

```
マイドライブ/
└── kyotei_prediction/     ← プロジェクト用ルート
    ├── data/
    │   └── raw/           ← 取得データを置く（2026-01/, 2026-02/ など）
    ├── optuna_models/     ← 学習後に Colab が保存
    ├── optuna_results/
    ├── optuna_logs/
    └── outputs/           ← 予測結果
```

- Drive の Web またはアプリで `kyotei_prediction/data/raw` まで作成しておく。
- 取得が終わったら、ローカルの `kyotei_predictor/data/raw/` の中身をここにアップロードする（または後述の同期ツールを使う）。

### 1-2. Colab 用ノートブック

リポジトリが **Drive 上にある**前提です。Colab では **clone 不要**で、Drive マウント後にそのフォルダを開いて実行します。

| ファイル | 用途 |
|----------|------|
| `colab_drive_learning_cycle_template.ipynb` | CPU で学習 |
| `colab_drive_learning_cycle_gpu_template.ipynb` | GPU で学習（推奨） |

- ノートブックの **PROJECT_DIR** を、Colab から見た Drive のリポジトリパスに合わせる（例: `'/content/drive/MyDrive/app/kyotei_Prediction'`）。
- データはリポジトリ内なら `PROJECT_DIR/kyotei_predictor/data/raw` を参照します。
- **依存関係**: Colab では `requirements-colab.txt` を使用します（torch/tensorboard は Colab 既存のものを利用し、競合を減らします）。

### 1-5. インストール後の「依存関係の競合」メッセージについて

`pip install` のあとに `ERROR: pip's dependency resolver... dependency conflicts` と出ることがあります。

- **ノートブックを `requirements-colab.txt` に変更済み**なので、torch/tensorboard の上書きは起こりにくくなっています。
- それでも他パッケージ（jax, tensorflow, google-colab など）との競合表示は出ることがあります。**本プロジェクトの学習ではそれらは使っていない**ため、多くの場合は無視して問題ありません。
- **「Restart the runtime」** と出たら、**ランタイムを再起動**してから、次のセル（変数設定・学習）を実行してください。

### 1-3. 実行する Colab の流れ

1. **Drive マウント**  
   `drive.mount('/content/drive')`
2. **Drive 上のリポジトリに移動**  
   `PROJECT_DIR` をあなたのパスに合わせてから、そのセルで `os.chdir(PROJECT_DIR)` と `pip install -r requirements.txt`
3. **変数設定**  
   `DRIVE_ROOT`（データ・成果物のルート）, `DATA_DIR`, `YEAR_MONTH`, `PREDICT_DATE`, `N_TRIALS`, `MINIMAL` など
4. **（任意）Colab で取得**  
   `RUN_FETCH = True` にすると Colab 上で取得。通常は `False` で Drive の既存データを使う。
5. **学習・予測**  
   `scripts/run_colab_learning_cycle.py` を実行

詳細: [Google Drive保存 + Colab学習ワークフロー](google_drive_colab_workflow.md)

### 1-4. git clone について（参考）

リポジトリが Drive にない環境で Colab を使う場合は、従来どおり GitHub から clone（または ZIP 取得）する方法もあります。その場合はテンプレートの「clone 用」セルを使うか、別ノートブックを参照してください。**Drive にリポジトリがある場合は clone は不要**です。

---

## 2. データ取得完了後にやること

### 2-1. 取得データを Drive に置く

ローカルで取得した `kyotei_predictor/data/raw/` を、Drive の `kyotei_prediction/data/raw/` に反映する。

**方法A: 手動**

- `kyotei_predictor/data/raw/` の中身（例: `2026-01/`, `2026-02/`）を ZIP で固めるか、フォルダごと Drive の `kyotei_prediction/data/raw/` にアップロードする。

**方法B: Drive がマウントされている環境で同期**

```bash
python -m kyotei_predictor.tools.storage.drive_data_sync \
  --direction push \
  --local-dir kyotei_predictor/data/raw \
  --drive-dir "/path/to/GoogleDrive/kyotei_prediction/data/raw"
```

- `/path/to/GoogleDrive` は実際の Drive マウント先（例: macOS の `/Volumes/GoogleDrive/マイドライブ`）に置き換える。

### 2-2. Colab でノートブックの変数を合わせる

- **DRIVE_ROOT**: `'/content/drive/MyDrive/kyotei_prediction'`（Drive のフォルダ名が `kyotei_prediction` の場合）
- **DATA_DIR**: `f'{DRIVE_ROOT}/data/raw'`
- **YEAR_MONTH**: 使いたい年月（例: `'2026-02'`）
- **PREDICT_DATE**: 予測したい日（例: `'2026-02-14'`）
- **N_TRIALS**: Optuna の試行回数（最初は `1` で確認推奨）
- **MINIMAL**: `True` で短時間検証、本番は `False`

### 2-3. Colab で上から順に実行

1. Drive マウント
2. PROJECT_DIR を合わせてから「リポジトリに移動 + pip install」
3. 変数セルを実行
4. 学習・予測のセルを実行

実行後、`optuna_models/` や `outputs/` が Drive の `kyotei_prediction/` 以下に保存されていれば準備完了。

---

## 3. 参照ドキュメント

- [Google Drive保存 + Colab学習ワークフロー](google_drive_colab_workflow.md)
- [処理の流れ（運用フロー）](processing_flow.md)
- [Cursor Web で取得したデータを Drive に保存する](cursor_web_drive_upload.md)
