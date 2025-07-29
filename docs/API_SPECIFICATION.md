# API仕様書

**最終更新日**: 2025-01-27  
**バージョン**: 4.1（リファクタリング完了）

---

## 🎯 概要

このドキュメントは、kyotei_Predictionプロジェクトの統合ユーティリティAPIの仕様を定義します。リファクタリング完了後の新しいアーキテクチャに基づいています。

---

## 📋 API概要

### 統合ユーティリティAPI
- **KyoteiUtils**: 基本ユーティリティ
- **Config**: 設定管理
- **Logger**: ログ機能
- **VenueMapper**: 会場マッピング
- **Exceptions**: エラーハンドリング

---

## 🔧 KyoteiUtils API

### 基本ユーティリティクラス

#### クラス定義
```python
class KyoteiUtils:
    """競艇予測システムの基本ユーティリティクラス"""
```

#### メソッド一覧

##### `load_json(file_path: str) -> Dict[str, Any]`
JSONファイルを読み込みます。

**パラメータ:**
- `file_path` (str): JSONファイルのパス

**戻り値:**
- `Dict[str, Any]`: 読み込んだJSONデータ

**例外:**
- `FileNotFoundError`: ファイルが見つからない場合
- `JSONDecodeError`: JSON形式が不正な場合

**使用例:**
```python
data = KyoteiUtils.load_json("data.json")
```

##### `save_json(data: Dict[str, Any], file_path: str) -> None`
データをJSONファイルに保存します。

**パラメータ:**
- `data` (Dict[str, Any]): 保存するデータ
- `file_path` (str): 保存先ファイルパス

**戻り値:**
- `None`

**例外:**
- `IOError`: ファイル書き込みエラーの場合

**使用例:**
```python
KyoteiUtils.save_json(data, "output.json")
```

##### `process_data(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]`
生データを処理します。

**パラメータ:**
- `raw_data` (List[Dict[str, Any]]): 生データ

**戻り値:**
- `List[Dict[str, Any]]`: 処理済みデータ

**使用例:**
```python
processed_data = KyoteiUtils.process_data(raw_data)
```

##### `calculate_metric(data: List[Dict[str, Any]]) -> float`
メトリックを計算します。

**パラメータ:**
- `data` (List[Dict[str, Any]]): 計算対象データ

**戻り値:**
- `float`: 計算結果

**使用例:**
```python
metric = KyoteiUtils.calculate_metric(data)
```

---

## ⚙️ Config API

### 設定管理クラス

#### クラス定義
```python
class Config:
    """競艇予測システムの設定管理クラス"""
```

#### メソッド一覧

##### `__init__(config_file: Optional[str] = None)`
設定クラスを初期化します。

**パラメータ:**
- `config_file` (Optional[str]): 設定ファイルのパス（デフォルト: None）

**使用例:**
```python
config = Config()
config = Config("custom_config.json")
```

##### `get_data_dir() -> str`
データディレクトリのパスを取得します。

**戻り値:**
- `str`: データディレクトリのパス

**使用例:**
```python
data_dir = config.get_data_dir()
```

##### `get_api_timeout() -> int`
APIタイムアウト値を取得します。

**戻り値:**
- `int`: タイムアウト値（秒）

**使用例:**
```python
timeout = config.get_api_timeout()
```

##### `get_log_level() -> str`
ログレベルを取得します。

**戻り値:**
- `str`: ログレベル

**使用例:**
```python
log_level = config.get_log_level()
```

##### `get(key: str, default: Any = None) -> Any`
カスタム設定値を取得します。

**パラメータ:**
- `key` (str): 設定キー
- `default` (Any): デフォルト値

**戻り値:**
- `Any`: 設定値

**使用例:**
```python
value = config.get("custom_key", default="default_value")
```

---

## 📝 Logger API

### ログ機能

#### 関数定義
```python
def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = "INFO",
    format_string: Optional[str] = None
) -> logging.Logger:
    """ロガーを設定します"""
```

#### パラメータ
- `name` (str): ロガー名
- `log_file` (Optional[str]): ログファイルパス（デフォルト: None）
- `level` (str): ログレベル（デフォルト: "INFO"）
- `format_string` (Optional[str]): ログフォーマット（デフォルト: None）

#### 戻り値
- `logging.Logger`: 設定されたロガー

#### 使用例
```python
logger = setup_logger("my_module", log_file="logs/app.log")
logger.info("処理開始")
logger.warning("警告メッセージ")
logger.error("エラーメッセージ")
```

---

## 🏟️ VenueMapper API

### 会場マッピングクラス

#### クラス定義
```python
class VenueMapper:
    """競艇会場のマッピング機能を提供するクラス"""
```

#### メソッド一覧

##### `get_venue_name(stadium_code: StadiumTelCode) -> str`
会場コードから会場名を取得します。

**パラメータ:**
- `stadium_code` (StadiumTelCode): 会場コード

**戻り値:**
- `str`: 会場名

**使用例:**
```python
venue_name = VenueMapper.get_venue_name(StadiumTelCode.KIRYU)
```

##### `get_venue_code(stadium_code: StadiumTelCode) -> str`
会場コードから会場コード文字列を取得します。

**パラメータ:**
- `stadium_code` (StadiumTelCode): 会場コード

**戻り値:**
- `str`: 会場コード文字列

**使用例:**
```python
venue_code = VenueMapper.get_venue_code(StadiumTelCode.KIRYU)
```

##### `get_venues_by_region(region: str) -> List[StadiumTelCode]`
地域別の会場リストを取得します。

**パラメータ:**
- `region` (str): 地域名

**戻り値:**
- `List[StadiumTelCode]`: 会場コードのリスト

**使用例:**
```python
kanto_venues = VenueMapper.get_venues_by_region("関東")
```

---

## ⚠️ Exceptions API

### カスタム例外クラス

#### 基本例外クラス
```python
class KyoteiError(Exception):
    """競艇予測システムの基本例外クラス"""
```

#### データ関連例外
```python
class DataError(KyoteiError):
    """データ処理に関する例外"""
```

#### API関連例外
```python
class APIError(KyoteiError):
    """API処理に関する例外"""
```

#### 設定関連例外
```python
class ConfigError(KyoteiError):
    """設定処理に関する例外"""
```

### エラーハンドリングデコレータ

#### 関数定義
```python
def handle_exception(func: Callable) -> Callable:
    """例外処理デコレータ"""
```

#### 使用例
```python
@handle_exception
def my_function():
    # 処理
    pass
```

---

## 🔄 移行ガイド

### 既存コードからの移行

#### 1. インポート文の変更
```python
# 移行前
from tools.common import get_config, setup_logging
from utils.common import process_data

# 移行後
from kyotei_predictor.utils import (
    Config, setup_logger, KyoteiUtils, handle_exception
)
```

#### 2. 設定管理の変更
```python
# 移行前
config = get_config()

# 移行後
config = Config()
```

#### 3. ログ機能の変更
```python
# 移行前
logger = setup_logging("my_module")

# 移行後
logger = setup_logger("my_module", log_file="logs/app.log")
```

#### 4. エラーハンドリングの変更
```python
# 移行前
try:
    # 処理
    pass
except Exception as e:
    logger.error(f"エラー: {e}")

# 移行後
@handle_exception
def my_function():
    # 処理
    pass
```

---

## 📊 パフォーマンス仕様

### メモリ使用量
- **設定管理**: 最小限のメモリ使用量
- **ログ機能**: ログローテーションによる自動クリーンアップ
- **データ処理**: 効率的なデータ構造の使用

### 処理速度
- **JSON操作**: 高速なJSON読み書き
- **設定取得**: キャッシュ機能による高速化
- **会場マッピング**: 事前定義されたマッピングによる高速検索

### スケーラビリティ
- **並列処理対応**: スレッドセーフな実装
- **拡張性**: プラグイン対応の設計
- **保守性**: モジュール化された構造

---

## 🧪 テスト仕様

### 単体テスト
- **KyoteiUtils**: JSON操作・データ処理・計算機能のテスト
- **Config**: 設定読み込み・環境変数・ファイル操作のテスト
- **VenueMapper**: 会場マッピング・地域別取得・コード変換のテスト
- **Exceptions**: カスタム例外・エラーハンドリングのテスト
- **Logger**: ログ設定・ファイル出力・レベル制御のテスト

### 統合テスト
- **全機能統合**: 統合ユーティリティ全体の動作テスト
- **エラー処理**: 例外処理の統合テスト
- **パフォーマンス**: 処理速度・メモリ使用量のテスト

---

## 📋 今後の拡張計画

### Phase 2: 既存コードの移行
1. **データ取得ツールの移行**
2. **バッチ処理の移行**
3. **予測エンジンの移行**

### Phase 3: パフォーマンス最適化
1. **キャッシュ機能の実装**
2. **並列処理の最適化**
3. **メモリ使用量の最適化**

### Phase 4: 機能拡張
1. **新しいユーティリティの追加**
2. **API機能の拡張**
3. **プラグインシステムの実装**

---

**最終更新**: 2025-01-27  
**次回更新予定**: 2025-02-03 