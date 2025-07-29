# 運用マニュアル

**最終更新日**: 2025-01-27  
**バージョン**: 4.2

---

## 概要

競艇予測システムの運用マニュアルです。システムの起動、監視、保守、トラブルシューティングについて説明しています。

---

## システム構成

### ディレクトリ構造

```
kyotei_predictor/
├── app.py                          # Webアプリケーション
├── config/                         # 設定ファイル
│   ├── config.json                # 基本設定
│   └── README.md                  # 設定ドキュメント
├── utils/                         # 統合ユーティリティ
│   ├── __init__.py               # 統合エントリーポイント
│   ├── common.py                 # 基本ユーティリティ
│   ├── config.py                 # 設定管理
│   ├── logger.py                 # ログ機能
│   ├── venue_mapping.py          # 会場マッピング
│   ├── exceptions.py             # エラーハンドリング
│   ├── cache.py                  # キャッシュ機能
│   ├── parallel.py               # 並列処理
│   └── memory.py                 # メモリ最適化
├── tools/                        # ツール群
│   ├── batch/                    # バッチ処理
│   ├── fetch/                    # データ取得
│   ├── analysis/                 # 分析ツール
│   └── optimization/             # 最適化ツール
├── data/                         # データディレクトリ
│   ├── raw/                      # 生データ
│   └── processed/                # 処理済みデータ
├── logs/                         # ログディレクトリ
└── cache/                        # キャッシュディレクトリ
```

---

## 起動手順

### 1. 環境準備

```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. 設定ファイルの確認

```bash
# 設定ファイルの存在確認
ls kyotei_predictor/config/config.json

# 設定内容の確認
cat kyotei_predictor/config/config.json
```

### 3. Webアプリケーションの起動

```bash
# 開発サーバーの起動
python kyotei_predictor/app.py

# 本番環境での起動
gunicorn -w 4 -b 0.0.0.0:5000 kyotei_predictor.app:app
```

### 4. バッチ処理の起動

```bash
# データ取得バッチ
python -m kyotei_predictor.tools.batch.batch_fetch_all_venues

# 予測実行バッチ
python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-01-15
```

---

## 監視項目

### 1. システム監視

#### メモリ使用量の監視

```python
from kyotei_predictor.utils import get_memory_info

# メモリ情報の取得
memory_info = get_memory_info()
print(f"プロセスメモリ: {memory_info['process_memory_mb']:.2f}MB")
print(f"システムメモリ使用率: {memory_info['system_memory']['percent']:.1f}%")
```

#### キャッシュ統計の監視

```python
from kyotei_predictor.utils import get_cache_manager

cache_manager = get_cache_manager()
stats = cache_manager.get_stats()
print(f"メモリキャッシュ数: {stats['memory_cache_count']}")
print(f"ファイルキャッシュ数: {stats['file_cache_count']}")
print(f"総キャッシュサイズ: {stats['total_size_mb']:.2f}MB")
```

### 2. ログ監視

#### ログファイルの確認

```bash
# ログディレクトリの確認
ls kyotei_predictor/logs/

# 最新ログの確認
tail -f kyotei_predictor/logs/app.log

# エラーログの確認
grep "ERROR" kyotei_predictor/logs/app.log
```

#### ログレベルの設定

```python
from kyotei_predictor.utils import setup_logger

# 詳細ログの設定
logger = setup_logger("monitoring", level="DEBUG")
logger.debug("詳細なデバッグ情報")
```

### 3. パフォーマンス監視

#### 実行時間の測定

```python
from kyotei_predictor.utils import measure_performance

# 関数の実行時間を測定
result, execution_time = measure_performance(my_function, arg1, arg2)
print(f"実行時間: {execution_time:.3f}秒")
```

#### 並列処理の監視

```python
from kyotei_predictor.utils import ParallelProcessor

processor = ParallelProcessor(max_workers=4)
results = processor.process_list(items, func, show_progress=True)
```

---

## 保守作業

### 1. 定期保守

#### キャッシュのクリーンアップ

```python
from kyotei_predictor.utils import get_cache_manager

cache_manager = get_cache_manager()

# 全キャッシュのクリア
cache_manager.clear()

# 特定キーの削除
cache_manager.delete("old_cache_key")
```

#### メモリ最適化

```python
from kyotei_predictor.utils import MemoryOptimizer

optimizer = MemoryOptimizer()

# メモリ最適化の実行
result = optimizer.optimize_memory(force_gc=True)
print(f"節約されたメモリ: {result['memory_saved_mb']:.2f}MB")
```

#### ログローテーション

```bash
# 古いログファイルの削除
find kyotei_predictor/logs/ -name "*.log" -mtime +30 -delete

# ログファイルの圧縮
gzip kyotei_predictor/logs/app.log.2024-01-01
```

### 2. データ保守

#### データ品質チェック

```bash
# データ品質チェックの実行
python -m kyotei_predictor.tools.data_quality_checker --daily-check
```

#### 欠損データの再取得

```bash
# 欠損データの再取得
python -m kyotei_predictor.tools.batch.retry_missing_races --start-date 2024-01-01 --end-date 2024-01-31
```

### 3. 設定管理

#### 設定の更新

```python
from kyotei_predictor.utils import Config

config = Config()

# 新しい設定の追加
config.set("new_setting", "value")

# 設定の確認
value = config.get("new_setting")
```

---

## トラブルシューティング

### 1. よくある問題

#### メモリ不足エラー

**症状**: `MemoryError` が発生

**対処法**:
```python
from kyotei_predictor.utils import MemoryOptimizer

optimizer = MemoryOptimizer()
optimizer.optimize_memory(force_gc=True)
```

#### キャッシュサイズ超過

**症状**: キャッシュディレクトリのサイズが大きくなる

**対処法**:
```python
from kyotei_predictor.utils import get_cache_manager

cache_manager = get_cache_manager()
cache_manager.clear()
```

#### 並列処理のエラー

**症状**: 並列処理でエラーが発生

**対処法**:
```python
from kyotei_predictor.utils import ParallelProcessor

# ワーカー数を減らす
processor = ParallelProcessor(max_workers=2)
```

### 2. ログ分析

#### エラーログの分析

```bash
# エラーログの抽出
grep "ERROR" kyotei_predictor/logs/app.log | tail -20

# 特定のエラーの検索
grep "MemoryError" kyotei_predictor/logs/app.log
```

#### パフォーマンスログの分析

```bash
# 実行時間の分析
grep "実行時間" kyotei_predictor/logs/app.log | awk '{print $NF}'

# メモリ使用量の分析
grep "メモリ使用量" kyotei_predictor/logs/app.log
```

### 3. システム診断

#### システム情報の取得

```python
from kyotei_predictor.utils import get_memory_info

# システム情報の取得
info = get_memory_info()
print(f"プロセスメモリ: {info['process_memory_mb']:.2f}MB")
print(f"システムメモリ使用率: {info['system_memory']['percent']:.1f}%")
```

#### パフォーマンステスト

```python
from kyotei_predictor.utils import optimize_parallel_processing

# 並列処理の最適化テスト
result = optimize_parallel_processing(test_function, test_data)
print(f"最適なワーカー数: {result['optimal_workers']}")
```

---

## バックアップ・復旧

### 1. データバックアップ

#### 設定ファイルのバックアップ

```bash
# 設定ファイルのバックアップ
cp kyotei_predictor/config/config.json backup/config_$(date +%Y%m%d).json
```

#### データファイルのバックアップ

```bash
# データディレクトリのバックアップ
tar -czf backup/data_$(date +%Y%m%d).tar.gz kyotei_predictor/data/
```

### 2. 復旧手順

#### 設定ファイルの復旧

```bash
# 設定ファイルの復旧
cp backup/config_20250127.json kyotei_predictor/config/config.json
```

#### データファイルの復旧

```bash
# データファイルの復旧
tar -xzf backup/data_20250127.tar.gz
```

---

## セキュリティ

### 1. アクセス制御

#### ファイル権限の設定

```bash
# 設定ファイルの権限設定
chmod 600 kyotei_predictor/config/config.json

# ログファイルの権限設定
chmod 644 kyotei_predictor/logs/*.log
```

#### 環境変数の管理

```bash
# 機密情報を環境変数で管理
export KYOTEI_API_KEY="your_api_key"
export KYOTEI_DB_PASSWORD="your_password"
```

### 2. ログセキュリティ

#### 機密情報の除外

```python
from kyotei_predictor.utils import setup_logger

# 機密情報を除外したログ設定
logger = setup_logger("secure_app", exclude_patterns=["password", "api_key"])
```

---

## 更新・アップグレード

### 1. バージョン管理

#### 現在のバージョン確認

```python
from kyotei_predictor.utils import KyoteiUtils

# バージョン情報の取得
version_info = KyoteiUtils.get_version_info()
print(f"現在のバージョン: {version_info['version']}")
```

#### アップグレード手順

```bash
# 新しいバージョンのダウンロード
git pull origin main

# 依存関係の更新
pip install -r requirements.txt --upgrade

# 設定ファイルの確認
diff kyotei_predictor/config/config.json backup/config_previous.json
```

### 2. 移行作業

#### データ移行

```python
from kyotei_predictor.utils import KyoteiUtils

# 古いデータ形式から新しい形式への移行
migrated_data = KyoteiUtils.migrate_data_format(old_data)
```

#### 設定移行

```python
from kyotei_predictor.utils import Config

# 古い設定から新しい設定への移行
config = Config()
config.migrate_from_old_format()
```

---

## サポート・連絡先

### 1. 問題報告

問題が発生した場合は、以下の情報を含めて報告してください：

- エラーメッセージ
- 実行環境（OS、Pythonバージョン）
- ログファイル
- 再現手順

### 2. ドキュメント

- [API仕様書](API_SPECIFICATION.md)
- [開発者ガイド](DEVELOPER_GUIDE.md)
- [テスト仕様書](TEST_SPECIFICATION.md)

---

**最終更新**: 2025-01-27  
**次回更新予定**: 2025-02-03