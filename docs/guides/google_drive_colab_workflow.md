# Google Drive保存 + Google Colab学習ワークフロー

## 準備チェックリスト

**データ取得を待っている間に進められる手順**は [Colab学習の準備チェックリスト](colab_learning_prep.md) にまとめています。

---

## 目的

- 取得データを Google Drive 側に保存
- Colab で Drive 上データを使って学習/予測
- 学習成果物（モデル・ログ・結果）を Drive に残す

## 1) 取得データをDriveへ保存（ローカル環境）

### A. 直接Drive配下へ保存（Driveがマウントされている場合）

```bash
python -m kyotei_predictor.tools.batch.batch_fetch_all_venues \
  --start-date 2026-02-01 \
  --end-date 2026-02-14 \
  --stadiums ALL \
  --output-data-dir "/content/drive/MyDrive/kyotei_prediction/data/raw"
```

### B. 既存データをDriveへ同期

```bash
python -m kyotei_predictor.tools.storage.drive_data_sync \
  --direction push \
  --local-dir kyotei_predictor/data/raw \
  --drive-dir /content/drive/MyDrive/kyotei_prediction/data/raw
```

## 2) Colabで学習/予測

### テンプレートノートブック

リポジトリにはそのまま実行できる Colab テンプレートを用意しています。

- `colab_drive_learning_cycle_template.ipynb`
- `colab_drive_learning_cycle_gpu_template.ipynb`（GPUランタイム向け）

ノートブックを Colab で開き、上から順に実行してください。

GPU向けテンプレートでは、パラメータセルでプリセットを切り替えられます。

- `quick_check`: 短時間の疎通確認（`--minimal` 相当）
- `night_train`: 夜間の長時間学習向け（試行回数を増加）

`PROFILE_NAME` を変更するだけで主要設定（試行回数/最小モード/取得期間）が切り替わります。

### 事前準備（Colabセル）

```python
from google.colab import drive
drive.mount('/content/drive')
```

```bash
cd /content
git clone https://github.com/takajin0114/kyotei_Prediction.git
cd kyotei_Prediction
pip install -r requirements.txt
```

### 実行（ラッパースクリプト）

```bash
python scripts/run_colab_learning_cycle.py \
  --drive-root /content/drive/MyDrive/kyotei_prediction \
  --year-month 2026-02 \
  --n-trials 1 \
  --minimal \
  --predict-date 2026-02-14
```

上記で以下を実行します:

1. Drive上 `data/raw` を使って学習
2. 指定日予測（`--predict-date` 指定時）
3. `optuna_models/`, `optuna_results/`, `optuna_logs/`, `outputs/` をDriveへ同期

## 3) 補助ツール

### Drive -> ローカル同期（pull）

```bash
python -m kyotei_predictor.tools.storage.drive_data_sync \
  --direction pull \
  --local-dir kyotei_predictor/data/raw \
  --drive-dir /content/drive/MyDrive/kyotei_prediction/data/raw
```

## 注意点

- `drive_data_sync` は「マウント済みのDriveパス」を通常ファイルコピーで同期します（Google Drive API認証は不要）。
- Colabの無料枠では学習が長時間になると途中終了する可能性があります。`--minimal` で短時間検証してから本番実行してください。
