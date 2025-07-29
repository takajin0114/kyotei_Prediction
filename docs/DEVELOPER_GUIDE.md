# 開発者ガイド

**最終更新日**: 2025-01-27  
**バージョン**: 4.1（リファクタリング完了）

---

## 🎯 概要

このガイドは、kyotei_Predictionプロジェクトの開発者向けドキュメントです。リファクタリング完了後の新しいアーキテクチャと統合ユーティリティの使用方法について説明します。

---

## 🏗️ 新しいアーキテクチャ

### 統合ユーティリティ構造
```
kyotei_predictor/utils/
├── __init__.py          # 統合エントリーポイント
├── common.py            # 基本ユーティリティ
├── config.py            # 設定管理
├── logger.py            # ログ機能
├── venue_mapping.py     # 会場マッピング
└── exceptions.py        # エラーハンドリング
```

### 主要コンポーネント
1. **KyoteiUtils**: 基本ユーティリティ（JSON操作・データ処理・計算機能）
2. **Config**: 設定管理（環境変数・設定ファイル・デフォルト値）
3. **Logger**: ログ機能（構造化ログ・ファイル出力・ローテーション）
4. **VenueMapper**: 会場マッピング（会場名・コード変換）
5. **Exceptions**: エラーハンドリング（カスタム例外・デコレータ）

---

## 🔧 使用方法

### 1. 基本インポート
```python
from kyotei_predictor.utils import (
    KyoteiUtils, Config, setup_logger, VenueMapper,
    KyoteiError, DataError, APIError, handle_exception
)
```

### 2. 設定管理
```python
# 設定インスタンスの作成
config = Config()

# 基本設定の取得
data_dir = config.get_data_dir()
api_timeout = config.get_api_timeout()
log_level = config.get_log_level()

# カスタム設定の取得
custom_value = config.get("custom_key", default="default_value")
```

### 3. ログ機能
```python
# ロガーの設定
logger = setup_logger(
    name="my_module",
    log_file="logs/app.log",
    level="INFO"
)

# ログ出力
logger.info("処理開始")
logger.warning("警告メッセージ")
logger.error("エラーメッセージ")
```

### 4. 会場マッピング
```python
from metaboatrace.models.stadium import StadiumTelCode

# 会場名の取得
venue_name = VenueMapper.get_venue_name(StadiumTelCode.KIRYU)

# 会場コードの取得
venue_code = VenueMapper.get_venue_code(StadiumTelCode.KIRYU)

# 地域別会場の取得
kanto_venues = VenueMapper.get_venues_by_region("関東")
```

### 5. エラーハンドリング
```python
# デコレータを使用したエラーハンドリング
@handle_exception
def my_function():
    # 処理
    pass

# カスタム例外の使用
try:
    # 処理
    pass
except DataError as e:
    logger.error(f"データエラー: {e}")
except APIError as e:
    logger.error(f"APIエラー: {e}")
```

### 6. 基本ユーティリティ
```python
# JSON操作
data = KyoteiUtils.load_json("data.json")
KyoteiUtils.save_json(data, "output.json")

# データ処理
processed_data = KyoteiUtils.process_data(raw_data)
calculated_value = KyoteiUtils.calculate_metric(data)
```

---

## 📋 開発ガイドライン

### 1. コード品質
- **型ヒント**: 全関数に型ヒントを追加
- **docstring**: 全クラス・メソッドにdocstringを追加
- **エラーハンドリング**: 適切な例外処理を実装
- **ログ出力**: 重要な処理にログを追加

### 2. 設定管理
- **環境変数**: 機密情報は環境変数で管理
- **設定ファイル**: デフォルト設定は`config.json`で管理
- **動的設定**: 実行時設定は`Config`クラスで管理

### 3. ログ機能
- **構造化ログ**: 重要な情報は構造化して出力
- **レベル制御**: 適切なログレベルを使用
- **ファイル出力**: ログファイルへの出力を設定

### 4. エラーハンドリング
- **カスタム例外**: 適切なカスタム例外を使用
- **デコレータ**: `@handle_exception`を活用
- **エラー情報**: 詳細なエラー情報を記録

### 5. テスト
- **単体テスト**: 各機能の単体テストを実装
- **統合テスト**: 統合ユーティリティのテストを実行
- **テストカバレッジ**: 十分なテストカバレッジを確保

---

## 🧪 テスト実行

### 基本テスト
```bash
# 全テストの実行
python -m pytest kyotei_predictor/tests/

# 特定のテストファイルの実行
python -m pytest kyotei_predictor/tests/test_utils.py

# カバレッジ付きテスト
python -m pytest --cov=kyotei_predictor kyotei_predictor/tests/
```

### 統合ユーティリティテスト
```bash
# 統合ユーティリティのテスト
python -m pytest kyotei_predictor/tests/test_utils.py -v
```

---

## 🔄 移行ガイド

### Phase 2: 既存コードの移行

#### 1. データ取得ツールの移行
```python
# 移行前
from tools.common import get_config, setup_logging

# 移行後
from kyotei_predictor.utils import Config, setup_logger
```

#### 2. バッチ処理の移行
```python
# 移行前
import logging
from tools.common import load_config

# 移行後
from kyotei_predictor.utils import Config, setup_logger, handle_exception
```

#### 3. 予測エンジンの移行
```python
# 移行前
from utils.common import process_data

# 移行後
from kyotei_predictor.utils import KyoteiUtils, handle_exception
```

---

## 📊 パフォーマンス最適化

### 1. キャッシュ機能
- **設定キャッシュ**: 設定値のキャッシュ機能
- **データキャッシュ**: 頻繁に使用するデータのキャッシュ
- **結果キャッシュ**: 計算結果のキャッシュ

### 2. 並列処理
- **マルチプロセス**: CPU負荷の高い処理
- **マルチスレッド**: I/O待ちの多い処理
- **非同期処理**: ネットワーク処理

### 3. メモリ最適化
- **メモリ使用量監視**: メモリ使用量の監視
- **ガベージコレクション**: 適切なメモリ解放
- **データ構造最適化**: 効率的なデータ構造の使用

---

## 🚀 今後の改善計画

### Phase 3: パフォーマンス最適化
1. **キャッシュ機能の実装**
2. **並列処理の最適化**
3. **メモリ使用量の最適化**

### Phase 4: ドキュメント整備
1. **API仕様書の作成**
2. **運用マニュアルの更新**
3. **開発者ガイドの充実**

---

## 📞 サポート

### 問題報告
- **GitHub Issues**: バグ報告・機能要望
- **ドキュメント**: 使用方法の確認
- **テスト**: 動作確認・デバッグ

### 貢献方法
- **プルリクエスト**: コード改善の提案
- **ドキュメント**: ドキュメントの改善
- **テスト**: テストケースの追加

---

**最終更新**: 2025-01-27  
**次回更新予定**: 2025-02-03 