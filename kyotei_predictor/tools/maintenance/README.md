# メンテナンスツール

自動クリーンアップとディスク容量監視システム

## 📋 概要

このディレクトリには、プロジェクトの自動メンテナンスを行うためのツールが含まれています。

### **主要機能**
- **自動クリーンアップ**: 古いファイルの自動削除
- **ディスク容量監視**: リアルタイム容量監視
- **定期実行スケジューラ**: 自動化されたメンテナンス

## 🛠️ ツール一覧

### **1. 自動クリーンアップ (`auto_cleanup.py`)**

古いファイルを自動的に削除し、ディスク容量を最適化します。

#### **使用方法**
```bash
# 基本的なクリーンアップ実行
python kyotei_predictor/tools/maintenance/auto_cleanup.py

# レポートのみ生成
python kyotei_predictor/tools/maintenance/auto_cleanup.py --report-only

# 設定ファイルを指定
python kyotei_predictor/tools/maintenance/auto_cleanup.py --config cleanup_config.json
```

#### **機能**
- ログファイルの自動削除（最新10個を保持）
- チェックポイントファイルの整理（最新5個を保持）
- アーカイブファイルの整理
- 一時ファイルの削除
- trialディレクトリの整理

### **2. ディスク容量監視 (`disk_monitor.py`)**

ディスク容量をリアルタイムで監視し、警告を発行します。

#### **使用方法**
```bash
# 現在のステータスを表示
python kyotei_predictor/tools/maintenance/disk_monitor.py --status

# レポートを生成
python kyotei_predictor/tools/maintenance/disk_monitor.py --report

# デーモンモードで実行
python kyotei_predictor/tools/maintenance/disk_monitor.py --daemon
```

#### **機能**
- ディスク使用率の監視
- ディレクトリサイズの監視
- 警告・危険・緊急レベルのアラート
- 履歴の保持

### **3. 定期実行スケジューラ (`scheduler.py`)**

自動クリーンアップとディスク監視を定期実行します。

#### **使用方法**
```bash
# 現在のステータスを表示
python kyotei_predictor/tools/maintenance/scheduler.py --status

# 即座にクリーンアップを実行
python kyotei_predictor/tools/maintenance/scheduler.py --run-now

# デーモンモードで実行
python kyotei_predictor/tools/maintenance/scheduler.py --daemon
```

#### **機能**
- 日次クリーンアップ（毎日02:00）
- 週次クリーンアップ（毎週日曜03:00）
- ディスク監視（30分間隔）
- 緊急クリーンアップ（容量超過時）

## ⚙️ 設定ファイル

### **1. クリーンアップ設定 (`cleanup_config.json`)**

```json
{
  "max_disk_usage_percent": 80,
  "targets": {
    "outputs/logs": {
      "enabled": true,
      "max_files": 10,
      "max_size_mb": 100
    },
    "optuna_models/graduated_reward_checkpoints": {
      "enabled": true,
      "max_files": 5,
      "max_size_mb": 500
    }
  }
}
```

### **2. 監視設定 (`monitor_config.json`)**

```json
{
  "monitoring": {
    "check_interval": 60,
    "warning_threshold": 70,
    "critical_threshold": 85,
    "emergency_threshold": 95
  },
  "directories": {
    "optuna_models": {"max_size_gb": 5},
    "optuna_logs": {"max_size_gb": 2}
  }
}
```

### **3. スケジューラ設定 (`scheduler_config.json`)**

```json
{
  "schedules": {
    "daily_cleanup": {
      "enabled": true,
      "time": "02:00"
    },
    "weekly_cleanup": {
      "enabled": true,
      "day": "sunday",
      "time": "03:00"
    }
  }
}
```

## 📊 監視対象

### **ディスク容量**
- **警告レベル**: 70%
- **危険レベル**: 85%
- **緊急レベル**: 95%

### **ディレクトリサイズ制限**
- `optuna_models`: 5GB
- `optuna_logs`: 2GB
- `optuna_tensorboard`: 3GB
- `outputs`: 1GB
- `archives`: 10GB

## 🔧 セットアップ

### **1. 依存関係のインストール**
```bash
pip install schedule psutil
```

### **2. 設定ファイルの確認**
各設定ファイルが正しく配置されていることを確認してください。

### **3. 初回実行**
```bash
# ディスク監視のテスト
python kyotei_predictor/tools/maintenance/disk_monitor.py --status

# クリーンアップのテスト
python kyotei_predictor/tools/maintenance/auto_cleanup.py --report-only
```

## 🚀 運用開始

### **1. 手動実行**
```bash
# クリーンアップ実行
python kyotei_predictor/tools/maintenance/auto_cleanup.py

# ディスク監視開始
python kyotei_predictor/tools/maintenance/disk_monitor.py --daemon
```

### **2. 自動実行**
```bash
# スケジューラ開始
python kyotei_predictor/tools/maintenance/scheduler.py --daemon
```

## 📈 レポート

### **生成されるレポート**
- `cleanup_report.json`: クリーンアップ実行結果
- `disk_monitor_report.json`: ディスク監視結果
- `auto_cleanup.log`: クリーンアップログ
- `disk_monitor.log`: 監視ログ
- `scheduler.log`: スケジューラログ

### **レポートの確認**
```bash
# クリーンアップレポート
cat cleanup_report.json

# ディスク監視レポート
cat disk_monitor_report.json
```

## ⚠️ 注意事項

### **1. バックアップ**
- 重要なファイルは事前にバックアップを取得してください
- 設定ファイルで削除対象を慎重に設定してください

### **2. 実行時間**
- クリーンアップは深夜（02:00-03:00）に実行されます
- 大量のファイルがある場合、処理に時間がかかる場合があります

### **3. ログ管理**
- ログファイルは自動的にローテーションされます
- 古いログは自動的に削除されます

## 🔍 トラブルシューティング

### **よくある問題**

#### **1. 権限エラー**
```bash
# 管理者権限で実行
sudo python kyotei_predictor/tools/maintenance/auto_cleanup.py
```

#### **2. 依存関係エラー**
```bash
# 依存関係を再インストール
pip install -r requirements.txt
```

#### **3. 設定ファイルエラー**
```bash
# 設定ファイルの構文チェック
python -m json.tool cleanup_config.json
```

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. **ログファイルの確認**
   - `auto_cleanup.log`
   - `disk_monitor.log`
   - `scheduler.log`

2. **設定ファイルの確認**
   - 各設定ファイルの構文
   - パスの設定

3. **システムリソースの確認**
   - ディスク容量
   - メモリ使用量
   - CPU使用率 