# 開発者ガイド

**最終更新日**: 2025-01-27  
**バージョン**: 4.2

---

## 概要

競艇予測システムの開発者ガイドです。開発環境のセットアップ、コーディング規約、テスト方法、デバッグ手法について説明しています。

---

## 開発環境のセットアップ

### 1. 必要なソフトウェア

- Python 3.8以上
- Git
- IDE（VSCode推奨）
- 仮想環境管理ツール

### 2. 環境構築

```bash
# リポジトリのクローン
git clone https://github.com/your-repo/kyotei_Prediction.git
cd kyotei_Prediction

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# 開発用依存関係のインストール
pip install -r requirements-dev.txt
```

### 3. IDE設定

#### VSCode設定

```json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true
}
```

---

## コーディング規約

### 1. Python規約

#### PEP 8準拠

```python
# インポート順序
import os
import sys
from typing import Dict, List, Optional

# クラス定義
class MyClass:
    """クラスの説明"""
    
    def __init__(self, param: str) -> None:
        """初期化メソッド"""
        self.param = param
    
    def my_method(self, arg: int) -> bool:
        """メソッドの説明"""
        return arg > 0
```

#### 型ヒントの使用

```python
from typing import Dict, List, Optional, Union

def process_data(
    data: List[Dict[str, Any]], 
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Union[int, float]]:
    """データ処理関数"""
    pass
```

### 2. ドキュメント規約

#### docstringの記述

```python
def calculate_probability(
    data: List[float], 
    method: str = "softmax"
) -> List[float]:
    """
    確率を計算する関数
    
    Args:
        data: 入力データのリスト
        method: 計算方法 ("softmax" または "normalize")
    
    Returns:
        計算された確率のリスト
    
    Raises:
        ValueError: 無効なmethodが指定された場合
    
    Example:
        >>> calculate_probability([1, 2, 3])
        [0.09003057317038046, 0.24472847105479764, 0.6652409557748219]
    """
    pass
```

### 3. エラーハンドリング

#### 例外処理の実装

```python
from kyotei_predictor.utils import KyoteiError, DataError

def safe_data_processing(data: Dict[str, Any]) -> Dict[str, Any]:
    """安全なデータ処理"""
    try:
        # データ処理
        result = process_data(data)
        return result
    except KeyError as e:
        raise DataError(f"必要なキーが見つかりません: {e}")
    except ValueError as e:
        raise KyoteiError(f"データ形式が不正です: {e}")
```

---

## 統合ユーティリティの使用

### 1. 基本ユーティリティ

#### KyoteiUtilsの使用

```python
from kyotei_predictor.utils import KyoteiUtils

# JSON操作
data = KyoteiUtils.load_json_file("data.json")
KyoteiUtils.save_json_file(data, "output.json")

# 確率計算
probs = [1, 2, 3, 4, 5]
normalized = KyoteiUtils.normalize_probabilities(probs)
softmax_result = KyoteiUtils.softmax(probs)

# データ検証
is_valid = KyoteiUtils.validate_race_data(race_data)
```

#### Configの使用

```python
from kyotei_predictor.utils import Config

config = Config()

# 設定取得
data_dir = config.get_data_dir()
timeout = config.get_api_timeout()

# カスタム設定
custom_value = config.get("custom_key", default="default_value")
```

### 2. キャッシュ機能

#### キャッシュマネージャーの使用

```python
from kyotei_predictor.utils import CacheManager, cache_result

# キャッシュマネージャーの初期化
cache_manager = CacheManager(cache_dir="cache", max_size_mb=100)

# データの保存・取得
cache_manager.set("key", data, max_age_seconds=3600)
cached_data = cache_manager.get("key", max_age_seconds=3600)

# キャッシュデコレータ
@cache_result(max_age_seconds=3600)
def expensive_function(param1: str, param2: int) -> Dict[str, Any]:
    """重い処理をキャッシュする関数"""
    # 重い処理
    return result
```

### 3. 並列処理

#### 並列処理マネージャーの使用

```python
from kyotei_predictor.utils import ParallelProcessor, parallelize

# 並列処理マネージャー
processor = ParallelProcessor(max_workers=4, use_processes=False)

# リストの並列処理
items = [1, 2, 3, 4, 5]
results = processor.process_list(items, lambda x: x * 2)

# 並列化デコレータ
@parallelize(max_workers=4, use_processes=False)
def process_item(item: Any) -> Any:
    """各アイテムの処理"""
    return processed_item
```

### 4. メモリ最適化

#### メモリ監視・最適化

```python
from kyotei_predictor.utils import (
    MemoryMonitor, MemoryOptimizer, memory_efficient
)

# メモリ監視
monitor = MemoryMonitor()
memory_mb = monitor.get_memory_usage()
monitor.log_memory_usage("処理前")

# メモリ最適化
optimizer = MemoryOptimizer()
result = optimizer.optimize_memory(force_gc=True)

# メモリ効率的デコレータ
@memory_efficient(max_memory_mb=1000)
def memory_intensive_function(data: List[Any]) -> List[Any]:
    """メモリ集約的な処理"""
    return processed_data
```

---

## テスト開発

### 1. 単体テスト

#### テストファイルの作成

```python
# test_my_module.py
import pytest
from kyotei_predictor.utils import KyoteiUtils

def test_load_json_file():
    """JSONファイル読み込みのテスト"""
    # テストデータの準備
    test_data = {"key": "value"}
    
    # テスト実行
    result = KyoteiUtils.load_json_file("test.json")
    
    # アサーション
    assert result == test_data

def test_normalize_probabilities():
    """確率正規化のテスト"""
    probs = [1, 2, 3]
    normalized = KyoteiUtils.normalize_probabilities(probs)
    
    assert len(normalized) == 3
    assert abs(sum(normalized) - 1.0) < 1e-8
```

#### テストの実行

```bash
# 全テストの実行
pytest

# 特定のテストファイルの実行
pytest test_my_module.py

# 詳細出力での実行
pytest -v

# カバレッジ付きでの実行
pytest --cov=kyotei_predictor
```

### 2. 統合テスト

#### 統合テストの作成

```python
# test_integration.py
import pytest
from kyotei_predictor.utils import (
    KyoteiUtils, Config, setup_logger, VenueMapper
)

def test_full_workflow():
    """完全なワークフローのテスト"""
    # 設定の初期化
    config = Config()
    
    # ログの設定
    logger = setup_logger("test_module")
    
    # データ処理
    data = {"test": "data"}
    processed_data = KyoteiUtils.process_data(data)
    
    # 結果の検証
    assert processed_data is not None
    assert "test" in processed_data
```

### 3. パフォーマンステスト

#### パフォーマンステストの作成

```python
from kyotei_predictor.utils import measure_performance

def test_performance():
    """パフォーマンステスト"""
    def test_function():
        # テスト対象の処理
        return result
    
    # 実行時間の測定
    result, execution_time = measure_performance(test_function)
    
    # パフォーマンス要件の検証
    assert execution_time < 1.0  # 1秒以内
    assert result is not None
```

---

## デバッグ手法

### 1. ログデバッグ

#### ログの活用

```python
from kyotei_predictor.utils import setup_logger

logger = setup_logger("debug_module", level="DEBUG")

def debug_function(data: Dict[str, Any]) -> Dict[str, Any]:
    """デバッグ用関数"""
    logger.debug(f"入力データ: {data}")
    
    try:
        result = process_data(data)
        logger.debug(f"処理結果: {result}")
        return result
    except Exception as e:
        logger.error(f"エラーが発生: {e}")
        raise
```

### 2. メモリデバッグ

#### メモリ使用量の監視

```python
from kyotei_predictor.utils import get_memory_info

def memory_debug_function():
    """メモリデバッグ用関数"""
    # 処理前のメモリ情報
    before_info = get_memory_info()
    print(f"処理前メモリ: {before_info['process_memory_mb']:.2f}MB")
    
    # 重い処理
    heavy_processing()
    
    # 処理後のメモリ情報
    after_info = get_memory_info()
    print(f"処理後メモリ: {after_info['process_memory_mb']:.2f}MB")
    
    # メモリ使用量の差分
    memory_diff = after_info['process_memory_mb'] - before_info['process_memory_mb']
    print(f"メモリ使用量増加: {memory_diff:.2f}MB")
```

### 3. プロファイリング

#### プロファイリングの実装

```python
import cProfile
import pstats
from kyotei_predictor.utils import measure_performance

def profile_function():
    """プロファイリング対象の関数"""
    # プロファイリングの開始
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 対象処理の実行
    result, execution_time = measure_performance(target_function)
    
    # プロファイリングの停止
    profiler.disable()
    
    # 結果の出力
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # 上位10件を表示
    
    return result
```

---

## コードレビュー

### 1. レビューチェックリスト

#### 機能面

- [ ] 要件を満たしているか
- [ ] エラーハンドリングが適切か
- [ ] パフォーマンスは十分か
- [ ] セキュリティは考慮されているか

#### コード品質

- [ ] PEP 8に準拠しているか
- [ ] 型ヒントが適切か
- [ ] docstringが記述されているか
- [ ] 変数名・関数名が適切か

#### テスト

- [ ] 単体テストが書かれているか
- [ ] テストカバレッジは十分か
- [ ] 統合テストは必要か

### 2. レビューコメント例

```python
# 良い例
def calculate_win_rate(wins: int, total_races: int) -> float:
    """
    勝率を計算する
    
    Args:
        wins: 勝利回数
        total_races: 総レース数
    
    Returns:
        勝率（0.0-1.0）
    
    Raises:
        ValueError: total_racesが0以下の場合
    """
    if total_races <= 0:
        raise ValueError("総レース数は0より大きい必要があります")
    
    return wins / total_races

# 改善が必要な例
def calc_wr(w, t):  # 変数名が不明確
    """勝率計算"""  # docstringが不十分
    return w/t  # エラーハンドリングなし
```

---

## 継続的インテグレーション

### 1. CI/CD設定

#### GitHub Actions設定例

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest --cov=kyotei_predictor
    
    - name: Run linting
      run: |
        flake8 kyotei_predictor
        black --check kyotei_predictor
```

### 2. 品質チェック

#### コード品質チェック

```bash
# リンターの実行
flake8 kyotei_predictor

# フォーマッターの実行
black kyotei_predictor

# 型チェック
mypy kyotei_predictor

# セキュリティチェック
bandit -r kyotei_predictor
```

---

## ドキュメント作成

### 1. APIドキュメント

#### docstringの記述

```python
def predict_race(
    race_data: Dict[str, Any],
    algorithm: str = "comprehensive"
) -> Dict[str, Any]:
    """
    レース結果を予測する
    
    Args:
        race_data: レースデータ
            - entries: 出走表データ
            - weather: 天候データ
            - track_condition: トラック状態
        algorithm: 予測アルゴリズム
            - "basic": 基本アルゴリズム
            - "comprehensive": 総合アルゴリズム
            - "ml": 機械学習アルゴリズム
    
    Returns:
        予測結果
            - predictions: 予測結果のリスト
            - confidence: 信頼度
            - algorithm_used: 使用したアルゴリズム
    
    Raises:
        DataError: データが不正な場合
        PredictionError: 予測に失敗した場合
    
    Example:
        >>> race_data = {"entries": [...], "weather": {...}}
        >>> result = predict_race(race_data, "comprehensive")
        >>> print(result["predictions"])
        [{"combination": [1, 2, 3], "probability": 0.15}]
    """
    pass
```

### 2. README作成

#### READMEテンプレート

```markdown
# モジュール名

## 概要

このモジュールの概要を説明します。

## インストール

```bash
pip install -r requirements.txt
```

## 使用方法

```python
from kyotei_predictor.utils import MyModule

# 基本的な使用方法
result = MyModule.process_data(data)
```

## API

### `process_data(data: Dict[str, Any]) -> Dict[str, Any]`

データを処理する関数

**パラメータ:**
- `data`: 処理対象のデータ

**戻り値:**
- 処理結果

## テスト

```bash
pytest test_my_module.py
```

## ライセンス

MIT License
```

---

## トラブルシューティング

### 1. よくある問題

#### インポートエラー

**症状**: `ModuleNotFoundError` が発生

**対処法**:
```bash
# 仮想環境の確認
which python

# パスの確認
echo $PYTHONPATH

# 依存関係の再インストール
pip install -r requirements.txt --force-reinstall
```

#### メモリエラー

**症状**: `MemoryError` が発生

**対処法**:
```python
from kyotei_predictor.utils import MemoryOptimizer

optimizer = MemoryOptimizer()
optimizer.optimize_memory(force_gc=True)
```

#### テストエラー

**症状**: テストが失敗する

**対処法**:
```bash
# テストの詳細実行
pytest -v -s

# 特定のテストのみ実行
pytest test_specific.py::test_function

# デバッグモードで実行
pytest --pdb
```

### 2. デバッグツール

#### デバッガーの使用

```python
import pdb

def debug_function():
    # ブレークポイントの設定
    pdb.set_trace()
    
    # デバッグ対象の処理
    result = process_data(data)
    
    return result
```

#### ログデバッグ

```python
import logging

# 詳細ログの設定
logging.basicConfig(level=logging.DEBUG)

def debug_with_logs():
    logging.debug("処理開始")
    
    try:
        result = process_data(data)
        logging.debug(f"処理結果: {result}")
        return result
    except Exception as e:
        logging.error(f"エラー: {e}")
        raise
```

---

## ベストプラクティス

### 1. コード設計

#### 単一責任の原則

```python
# 良い例
class DataProcessor:
    """データ処理専用クラス"""
    def process_data(self, data):
        pass

class PredictionEngine:
    """予測専用クラス"""
    def predict(self, data):
        pass

# 悪い例
class KyoteiSystem:
    """全ての処理を行うクラス"""
    def process_data(self, data):
        pass
    
    def predict(self, data):
        pass
    
    def save_data(self, data):
        pass
```

#### 依存性注入

```python
# 良い例
class PredictionService:
    def __init__(self, data_processor, model):
        self.data_processor = data_processor
        self.model = model
    
    def predict(self, data):
        processed_data = self.data_processor.process(data)
        return self.model.predict(processed_data)

# 悪い例
class PredictionService:
    def predict(self, data):
        # 直接依存関係を作成
        processor = DataProcessor()
        model = Model()
        return model.predict(processor.process(data))
```

### 2. パフォーマンス

#### 効率的なデータ処理

```python
# 良い例
def process_large_dataset(data):
    # ジェネレータを使用
    for item in data:
        yield process_item(item)

# 悪い例
def process_large_dataset(data):
    # 全てのデータをメモリに保持
    results = []
    for item in data:
        results.append(process_item(item))
    return results
```

#### キャッシュの活用

```python
from kyotei_predictor.utils import cache_result

@cache_result(max_age_seconds=3600)
def expensive_calculation(data):
    # 重い計算処理
    return result
```

---

**最終更新**: 2025-01-27  
**次回更新予定**: 2025-02-03 