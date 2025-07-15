# kyotei_predictor/static ディレクトリ

## 概要
Web表示機能の静的ファイル（CSS、JavaScript）とテスト用HTTPサーバーを管理するディレクトリです。

## ファイル構成
- `predictions.css` - Web表示機能のスタイルシート
- `predictions.js` - Web表示機能のJavaScript（表示・フィルタリング・インタラクション）
- `test_server.py` - ローカルテスト用HTTPサーバー
- `stop_test_server.py` - テストサーバーの安全な停止スクリプト（新規追加）

## テストサーバーの運用

### 起動方法
```bash
python kyotei_predictor/static/test_server.py
```

### 停止方法

#### 1. 安全な停止（推奨）
```bash
python kyotei_predictor/static/stop_test_server.py
```

**特徴：**
- テストサーバープロセスのみを停止
- 他のバッチ処理やPythonプロセスに影響しない
- PIDファイル（`test_server.pid`）を自動管理

#### 2. 従来の方法
```bash
# Ctrl+C で手動停止
# または
taskkill /f /im python.exe  # 注意：全Pythonプロセスが停止
```

**注意：**
- `taskkill /f /im python.exe` は**全Pythonプロセス**を強制終了するため、
  データ取得バッチや他の重要なプロセスも停止してしまいます。
- 本番環境では使用を避けてください。

## 技術仕様

### test_server.py
- ポート8000でHTTPサーバーを起動
- プロジェクトルートをドキュメントルートとして設定
- 起動時に自身のPIDを`test_server.pid`に記録
- 終了時にPIDファイルを自動削除

### stop_test_server.py
- `test_server.pid`からPIDを読み取り
- Windows環境：`taskkill /PID <pid> /F`
- UNIX環境：`os.kill(pid, signal.SIGTERM)`
- 停止後にPIDファイルを削除

## 運用上の注意点

1. **テストサーバー起動時**
   - ポート8000が使用中でないことを確認
   - 他のバッチ処理と競合しないよう注意

2. **テストサーバー停止時**
   - 必ず`stop_test_server.py`を使用
   - `taskkill /f /im python.exe`は使用禁止

3. **PIDファイル管理**
   - `test_server.pid`は自動管理される
   - 手動で削除する必要はない

## トラブルシューティング

### ポート8000が使用中
```bash
# 使用中のプロセスを確認
netstat -an | findstr :8000

# 必要に応じて安全に停止
python kyotei_predictor/static/stop_test_server.py
```

### PIDファイルが残っている
```bash
# 手動で削除（通常は不要）
rm kyotei_predictor/static/test_server.pid
```

## 関連ドキュメント
- [../tests/README.md](../tests/README.md) - テスト実行方法
- [../templates/README.md](../templates/README.md) - HTMLテンプレート
- [../../docs/web_display_implementation.md](../../docs/web_display_implementation.md) - Web表示機能の実装詳細 