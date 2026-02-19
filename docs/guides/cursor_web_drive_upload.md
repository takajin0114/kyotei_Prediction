# Cursor Web で取得したデータを Google Drive に保存する

Cursor Web でプロジェクトを開いている場合、ワークスペースはクラウド上にあります。データ取得を実行すると結果は**そのワークスペース内**の `kyotei_predictor/data/raw` に保存されます。ここでは、その結果を **Google Drive に保存する**方法をまとめます。

---

## 2つの方法

| 方法 | 手軽さ | 手順 |
|------|--------|------|
| **A. 手動でダウンロード→Drive にアップロード** | 設定不要 | 取得後、ワークスペースの `kyotei_predictor/data/raw` をダウンロードし、Drive のフォルダにアップロードする |
| **B. アップロードスクリプト（Drive API）** | 初回のみ設定 | credentials を用意し、`drive_upload.py` を実行すると自動で Drive にアップロードする |

---

## 方法A: 手動で Drive に保存

1. Cursor Web でデータ取得を実行する（例: `python scripts/run_fetch_one_race.py` や `fetch_reperiod.bat` 相当のコマンド）。
2. 左のファイルツリーで **`kyotei_predictor/data/raw`** を右クリックし、**ダウンロード**（Download / Export）で ZIP などで保存。
3. スマホまたは PC で Google Drive を開き、**kyotei_prediction / data / raw** など保存したいフォルダに、ダウンロードした中身をアップロードする。

- **メリット**: 追加の設定や認証は不要。
- **デメリット**: 取得のたびに手動でダウンロード・アップロードが必要。

---

## 方法B: アップロードスクリプト（Drive API）で自動保存

取得後に **1コマンド** で、ワークスペースの `data/raw` を指定した Drive フォルダにアップロードできます。

### 1. 依存パッケージのインストール

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 2. Google Drive API の準備（初回のみ）

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成（または既存を選択）。
2. **API とサービス** → **ライブラリ** → 「Google Drive API」で検索 → **有効化**。
3. **API とサービス** → **認証情報** → **認証情報を作成** → **OAuth クライアント ID**。
   - アプリの種類: **デスクトップアプリ**（または「ウェブアプリケーション」で Cursor Web の制約に合わせる）。
   - 名前は任意。作成後、**JSON をダウンロード**。
4. ダウンロードした JSON を、プロジェクトルートで **`credentials.json`** という名前で保存（Cursor Web のワークスペースにアップロードして置いても可）。

### 3. 初回認証（token.json を作る）

**ブラウザが使える環境**（PC の Cursor や、Cursor Web でブラウザが開ける場合）で実行:

```bash
python -m kyotei_predictor.tools.storage.drive_upload --auth-only
```

ブラウザが開くので、保存先にしたい Google アカウントでログインし、権限を許可する。成功するとプロジェクト内に **`token.json`** が作成されます。Cursor Web だけを使う場合は、**一度 PC などでこの認証を実行し、`credentials.json` と `token.json` を Cursor Web のワークスペースに置く**と、以降は Cursor Web からアップロードできます。

### 4. 取得後に Drive へアップロード

データ取得を実行したあと、次を実行します。

```bash
python -m kyotei_predictor.tools.storage.drive_upload \
  --local-dir kyotei_predictor/data/raw \
  --drive-folder-name "kyotei_prediction/data/raw"
```

- `--local-dir`: アップロードしたいローカル（ワークスペース内）のフォルダ。
- `--drive-folder-name`: Drive の「マイドライブ」直下からのフォルダパス。存在しなければ作成されます。

オプションは `python -m kyotei_predictor.tools.storage.drive_upload --help` で確認できます。

---

## Cursor Web でのおすすめの流れ

1. **データ取得**  
   `python scripts/run_fetch_one_race.py` や、期間指定の取得コマンドを実行。
2. **Drive に保存**  
   - **手軽にやる**: 方法Aで `kyotei_predictor/data/raw` をダウンロードし、Drive にアップロード。  
   - **自動化する**: 方法Bの準備を済ませたうえで、`drive_upload` を実行。

これで、Cursor Web で取得した結果を Google Drive に保存できます。

---

## 関連ドキュメント

- [処理の流れ（全体）](processing_flow.md)
- [Google Drive 保存 + Colab 学習](google_drive_colab_workflow.md)
