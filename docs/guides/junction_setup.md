# Windows Junction による日本語パス回避

プロジェクトが Google Drive 等の日本語パス（例: `マイドライブ`）にある場合、コマンドプロンプトやツールによってはパスが正しく扱われないことがあります。**Junction** を使って日本語を含まないパスからプロジェクトにアクセスできます。

---

## 概要

| 項目 | 内容 |
|------|------|
| **Junction** | フォルダへの別名リンク（シンボリックリンクの一種） |
| **想定される設定例** | `C:\GDrive` → `C:\Users\<ユーザー>\マイドライブ` |
| **プロジェクトパス** | `C:\GDrive\app\kyotei_Prediction\kyotei_Prediction` |

---

## 既存の Junction の確認

すでに Junction を設定しているか確認するには、管理者権限でコマンドプロンプトを開き、次を実行します。

```cmd
dir C:\ /AD /AL
```

`<JUNCTION>` と表示され、`GDrive` などが `マイドライブ` を指していれば設定済みです。

---

## Junction の作成（未設定の場合）

管理者権限でコマンドプロンプトを開き、次を実行します。

```cmd
mklink /J "C:\GDrive" "C:\Users\<ユーザー名>\マイドライブ"
```

- `<ユーザー名>` を実際のユーザー名（例: `takaj`）に置き換える。
- Google Drive for Desktop で「マイドライブ」が同期されているパスを指定する（例: `C:\Users\takaj\マイドライブ`）。

作成後、`C:\GDrive` からプロジェクトにアクセスできます。

---

## プロジェクトへのアクセス

| 用途 | パス |
|------|------|
| プロジェクトルート | `C:\GDrive\app\kyotei_Prediction\kyotei_Prediction` |
| 1R 疎通確認 | `C:\GDrive\app\kyotei_Prediction\kyotei_Prediction\scripts\fetch_one_race.bat` |
| 1か月分取得 | `C:\GDrive\app\kyotei_Prediction\kyotei_Prediction\scripts\fetch_1month.bat` |
| 期間指定取得 | `C:\GDrive\app\kyotei_Prediction\kyotei_Prediction\scripts\fetch_reperiod.bat` |

### 実行例

```cmd
cd /d C:\GDrive\app\kyotei_Prediction\kyotei_Prediction
scripts\fetch_1month.bat
```

または PowerShell:

```powershell
Set-Location C:\GDrive\app\kyotei_Prediction\kyotei_Prediction
.\scripts\fetch_1month.bat
```

---

## 注意事項

- Junction は Windows の機能のため、管理者権限が必要です。
- Junction 先（`マイドライブ`）のフォルダを移動・削除すると、Junction は無効になります。
- 本番データや取得結果は元のフォルダ（`マイドライブ` 内）に保存されます。

---

## 関連ドキュメント

- [処理の流れ（運用フロー）](processing_flow.md)
- [バッチの使い方](batch_usage.md)
