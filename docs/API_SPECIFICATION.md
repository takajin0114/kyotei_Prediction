# API仕様書

**最終更新日**: 2025-01-27  
**バージョン**: 4.2

---

## 概要

競艇予測システムのAPI仕様書です。統合ユーティリティ、キャッシュ機能、並列処理、メモリ最適化機能の使用方法を記載しています。

---

## 統合ユーティリティ API

### 基本ユーティリティ

#### KyoteiUtils

```python
from kyotei_predictor.utils import KyoteiUtils

# JSON操作
data = KyoteiUtils.load_json_file("data.json")
success = KyoteiUtils.save_json_file(data, "output.json")

# 確率計算
probs = [1, 2, 3, 4, 5]
normalized = KyoteiUtils.normalize_probabilities(probs)
softmax_result = KyoteiUtils.softmax(probs)

# データ検証
is_valid = KyoteiUtils.validate_race_data(race_data)
```

#### Config

```python
from kyotei_predictor.utils import Config

config = Config()

# 設定取得
data_dir = config.get_data_dir()
timeout = config.get_api_timeout()
log_level = config.get_log_level()
```

#### VenueMapper

```python
from kyotei_predictor.utils import VenueMapper
from metaboatrace.models.stadium import StadiumTelCode

# 会場情報取得
venue_name = VenueMapper.get_venue_name(StadiumTelCode.KIRYU)
venue_code = VenueMapper.get_venue_code(StadiumTelCode.KIRYU)
region = VenueMapper.get_venue_region(StadiumTelCode.KIRYU)

# 全スタジアム取得
all_stadiums = VenueMapper.get_all_stadiums()
region_stadiums = VenueMapper.get_stadiums_by_region("関東")
```

#### Logger

```python
from kyotei_predictor.utils import setup_logger

logger = setup_logger("my_module", log_file="logs/app.log")
logger.info("情報メッセージ")
logger.warning("警告メッセージ")
logger.error("エラーメッセージ")
```

#### Exceptions

```python
from kyotei_predictor.utils import KyoteiError, DataError, APIError

# カスタム例外
raise KyoteiError("競艇システムエラー")
raise DataError("データ処理エラー")
raise APIError("API通信エラー")
```

---

## キャッシュ機能 API

### CacheManager

```python
from kyotei_predictor.utils import CacheManager

# キャッシュマネージャー初期化
cache_manager = CacheManager(cache_dir="cache", max_size_mb=100)

# データの保存・取得
cache_manager.set("key", data, max_age_seconds=3600)
cached_data = cache_manager.get("key", max_age_seconds=3600)

# キャッシュ管理
cache_manager.delete("key")
cache_manager.clear()

# 統計情報取得
stats = cache_manager.get_stats()
```

### グローバルキャッシュマネージャー

```python
from kyotei_predictor.utils import get_cache_manager

cache_manager = get_cache_manager()
cached_data = cache_manager.get("key")
```

### キャッシュデコレータ

```python
from kyotei_predictor.utils import cache_result

@cache_result(max_age_seconds=3600)
def expensive_function(param1, param2):
    # 重い処理
    return result
```

---

## 並列処理 API

### ParallelProcessor

```python
from kyotei_predictor.utils import ParallelProcessor

# 並列処理マネージャー初期化
processor = ParallelProcessor(max_workers=4, use_processes=False)

# リストの並列処理
items = [1, 2, 3, 4, 5]
results = processor.process_list(items, lambda x: x * 2)

# 辞書の並列処理
data_dict = {"a": 1, "b": 2, "c": 3}
results = processor.process_dict(data_dict, lambda k, v: (k, v * 2))
```

### 並列化デコレータ

```python
from kyotei_predictor.utils import parallelize

@parallelize(max_workers=4, use_processes=False)
def process_item(item):
    # 各アイテムの処理
    return processed_item
```

### バッチ処理

```python
from kyotei_predictor.utils import batch_process

items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
results = batch_process(items, lambda x: x * 2, batch_size=3)
```

### パフォーマンス測定

```python
from kyotei_predictor.utils import measure_performance, get_optimal_workers

# 実行時間測定
result, execution_time = measure_performance(my_function, arg1, arg2)

# 最適なワーカー数取得
optimal_workers = get_optimal_workers(cpu_intensive=True)
```

---

## メモリ最適化 API

### MemoryMonitor

```python
from kyotei_predictor.utils import MemoryMonitor

monitor = MemoryMonitor()

# メモリ使用量取得
memory_mb = monitor.get_memory_usage()
memory_percent = monitor.get_memory_percentage()

# システムメモリ情報
system_info = monitor.get_system_memory_info()

# メモリ使用量ログ
monitor.log_memory_usage("処理前")

# 閾値チェック
is_over_threshold = monitor.check_memory_threshold(threshold_mb=1000)
```

### MemoryOptimizer

```python
from kyotei_predictor.utils import MemoryOptimizer

optimizer = MemoryOptimizer()

# メモリ最適化
optimization_result = optimizer.optimize_memory(force_gc=True)

# 関数監視
monitor_result = optimizer.monitor_function(my_function, arg1, arg2)
```

### メモリ効率的デコレータ

```python
from kyotei_predictor.utils import memory_efficient

@memory_efficient(max_memory_mb=1000)
def memory_intensive_function(data):
    # メモリ集約的な処理
    return result
```

### チャンク処理

```python
from kyotei_predictor.utils import chunk_processing

large_items = [1, 2, 3, ..., 10000]
results = chunk_processing(large_items, process_item, chunk_size=100)
```

### メモリ情報取得

```python
from kyotei_predictor.utils import get_memory_info

memory_info = get_memory_info()
print(f"プロセスメモリ: {memory_info['process_memory_mb']:.2f}MB")
print(f"システムメモリ使用率: {memory_info['system_memory']['percent']:.1f}%")
```

---

## Web API

### レースデータ取得

```
GET /api/race_data?date=2024-01-15&venue=KIRYU&race=1
```

**レスポンス例:**
```json
{
  "race_info": {
    "date": "2024-01-15",
    "venue": "KIRYU",
    "race_number": 1
  },
  "entries": [...],
  "results": [...]
}
```

### 予測実行

```
POST /api/predict
Content-Type: application/json

{
  "date": "2024-01-15",
  "venue": "KIRYU",
  "race": 1,
  "algorithm": "comprehensive"
}
```

**レスポンス例:**
```json
{
  "predictions": [
    {"combination": [1, 2, 3], "probability": 0.15},
    {"combination": [2, 1, 3], "probability": 0.12}
  ],
  "suggestions": [
    {"type": "straight", "combinations": [[1, 2, 3]]},
    {"type": "box", "combinations": [[1, 2, 3], [1, 3, 2]]}
  ]
}
```

---

## エラーハンドリング

### エラーコード

| コード | 説明 |
|--------|------|
| 400 | リクエストエラー |
| 404 | リソースが見つかりません |
| 500 | サーバーエラー |
| 503 | サービス利用不可 |

### エラーレスポンス例

```json
{
  "error": {
    "code": 400,
    "message": "不正なリクエスト",
    "details": "日付形式が正しくありません"
  }
}
```

---

## 使用例

### 完全な使用例

```python
from kyotei_predictor.utils import (
    KyoteiUtils, Config, setup_logger, VenueMapper,
    CacheManager, ParallelProcessor, MemoryOptimizer,
    cache_result, parallelize, memory_efficient
)

# ログ設定
logger = setup_logger("my_app")

# 設定取得
config = Config()
data_dir = config.get_data_dir()

# キャッシュ設定
cache_manager = CacheManager()

# メモリ最適化
optimizer = MemoryOptimizer()

@cache_result(max_age_seconds=3600)
@memory_efficient(max_memory_mb=1000)
def process_race_data(race_data):
    # レースデータ処理
    return processed_data

# 並列処理
processor = ParallelProcessor(max_workers=4)
results = processor.process_list(race_list, process_race_data)
```

---

## 更新履歴

- **v4.2 (2025-01-27)**: キャッシュ機能、並列処理、メモリ最適化機能を追加
- **v4.1 (2025-01-27)**: 統合ユーティリティの基本機能を追加
- **v4.0 (2025-01-27)**: 初回リリース 