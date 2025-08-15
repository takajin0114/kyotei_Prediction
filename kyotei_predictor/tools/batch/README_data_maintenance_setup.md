# データ取得前準備・実行一括バッチツール

## 概要
依存関係のインストールからデータ取得・品質チェックまで一括実行できるバッチツールです。

## 特徴
- **自動前準備**: 必要なPythonモジュールを自動インストール
- **環境チェック**: Pythonバージョン・仮想環境の確認
- **一括実行**: データ取得から品質チェックまで自動実行
- **エラーハンドリング**: 各ステップでのエラー処理と継続実行
- **ログ記録**: 詳細な実行ログの保存

## ファイル構成
```
kyotei_predictor/tools/batch/
├── run_data_maintenance_with_setup.py    # Pythonスクリプト（メイン）
├── run_data_maintenance_with_setup.bat   # Windowsバッチファイル
├── run_data_maintenance_with_setup.ps1   # PowerShellスクリプト
└── README_data_maintenance_setup.md      # このファイル
```

## 使用方法

### 1. Pythonスクリプト直接実行
```bash
# 仮想環境を有効化
venv\Scripts\Activate.ps1

# 2025年7月のデータ取得（前準備付き）
python -m kyotei_predictor.tools.batch.run_data_maintenance_with_setup --start-date 2025-07-01 --end-date 2025-07-31 --stadiums ALL

# 前準備をスキップ（既にインストール済みの場合）
python -m kyotei_predictor.tools.batch.run_data_maintenance_with_setup --start-date 2025-07-01 --end-date 2025-07-31 --stadiums ALL --skip-setup
```

### 2. Windowsバッチファイル実行
```cmd
# 引数付き実行
run_data_maintenance_with_setup.bat 2025-07-01 2025-07-31 ALL

# 対話式実行（引数なし）
run_data_maintenance_with_setup.bat
```

### 3. PowerShellスクリプト実行
```powershell
# 引数付き実行
.\run_data_maintenance_with_setup.ps1 -StartDate "2025-07-01" -EndDate "2025-07-31" -Stadiums "ALL"

# 対話式実行（引数なし）
.\run_data_maintenance_with_setup.ps1
```

## コマンドライン引数

| 引数 | 説明 | デフォルト値 |
|------|------|-------------|
| `--start-date` | 取得開始日 (YYYY-MM-DD) | なし（必須） |
| `--end-date` | 取得終了日 (YYYY-MM-DD) | なし（必須） |
| `--stadiums` | 対象会場 (ALL または カンマ区切り) | ALL |
| `--schedule-workers` | 開催日取得の並列数 | 8 |
| `--race-workers` | レース取得の並列数 | 16 |
| `--skip-setup` | 前準備（依存関係インストール）をスキップ | False |

## 実行フロー

### 1. 環境チェック
- Pythonバージョン確認（3.8以上推奨）
- 仮想環境の有効化確認

### 2. 前準備（依存関係インストール）
- ルートの`requirements.txt`インストール
- `kyotei_predictor/requirements.txt`インストール
- 重要モジュールの個別インストール
- インストール結果の検証

### 3. データメンテナンス実行
- データ取得（`batch_fetch_all_venues`）
- 取得状況サマリ（`list_fetched_data_summary`）
- 欠損データ再取得（`retry_missing_races`）
- データ品質チェック（`data_availability_checker`）

## ログファイル
実行ログは以下のパスに保存されます：
```
data/logs/data_maintenance_setup_YYYYMMDD_HHMMSS.log
```

## エラーハンドリング

### 依存関係インストールエラー
- インストールに失敗しても処理を継続
- 警告メッセージで問題を通知

### データ取得エラー
- 個別ステップの失敗を記録
- 後続のステップは継続実行

### 予期しないエラー
- 詳細なエラー情報をログに記録
- 適切な終了コードで終了

## 注意事項

1. **仮想環境**: 実行前に仮想環境を有効化してください
2. **管理者権限**: 一部のモジュールインストールに管理者権限が必要な場合があります
3. **ネットワーク**: インターネット接続が必要です
4. **ディスク容量**: 十分な空き容量を確保してください
5. **多重起動**: ロックファイルにより多重起動を防止しています

## トラブルシューティング

### モジュールインストールエラー
```bash
# pipのアップグレード
python -m pip install --upgrade pip

# 個別インストール
pip install requests metaboatrace pandas numpy
```

### 権限エラー
- 管理者権限でPowerShellを実行
- 仮想環境のパーミッションを確認

### ロックファイルエラー
```bash
# ロックファイルを削除
del run_data_maintenance_setup.lock
```

## 使用例

### 2025年7月のデータ取得
```bash
python -m kyotei_predictor.tools.batch.run_data_maintenance_with_setup --start-date 2025-07-01 --end-date 2025-07-31 --stadiums ALL
```

### 特定会場のみ（テスト用）
```bash
python -m kyotei_predictor.tools.batch.run_data_maintenance_with_setup --start-date 2025-07-01 --end-date 2025-07-31 --stadiums KIRYU
```

### 並列数調整
```bash
python -m kyotei_predictor.tools.batch.run_data_maintenance_with_setup --start-date 2025-07-01 --end-date 2025-07-31 --stadiums ALL --schedule-workers 4 --race-workers 8
```

このツールにより、データ取得の前準備から実行までを一括で自動化できます。
