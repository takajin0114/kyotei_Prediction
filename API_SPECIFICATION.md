# API仕様書

**作成日**: 2025-07-06  
**バージョン**: Phase 3  
**対象**: kyotei_Prediction システム全体

---

## 📋 概要

このドキュメントは、kyotei_Predictionシステムの主要なAPI、クラス、関数の仕様を定義します。

---

## 🏗 アーキテクチャ概要

### 主要コンポーネント
1. **データ取得層**: 公式サイトからのデータスクレイピング
2. **予測モデル層**: 着順依存型3連単モデル
3. **分析層**: 投資価値分析・統計検証
4. **Webアプリ層**: Flaskベースのユーザーインターフェース

---

## 📊 予測モデルAPI

### TrifectaDependentModel

**ファイル**: `kyotei_predictor/pipelines/trifecta_dependent_model.py`

#### クラス概要
着順依存性・艇間相関を考慮した3連単確率予測モデル

#### 主要メソッド

##### `learn_conditional_probabilities(data_dir: str, max_files: int = 1000) -> None`
条件付き確率・艇間相関を学習

**パラメータ:**
- `data_dir`: 学習データディレクトリ
- `max_files`: 最大学習ファイル数

**処理内容:**
- P(2着|1着)の学習
- P(3着|1着,2着)の学習
- 隣接艇パターンの学習
- コース特性の学習

##### `calculate_dependent_probabilities(race_data: Dict[str, Any]) -> Dict[str, Any]`
着順依存型3連単確率を計算

**パラメータ:**
- `race_data`: レースデータ

**戻り値:**
```json
{
  "predictions": [
    {
      "combination": "1-2-3",
      "probability": 0.125,
      "rank": 1
    }
  ],
  "top_combination": "1-2-3",
  "top_probability": 0.125,
  "model_info": {
    "model_type": "dependent_trifecta",
    "learning_races": 1000
  }
}
```

##### `save_model(file_path: str) -> bool`
学習済みモデルを保存

##### `load_model(file_path: str) -> bool`
学習済みモデルを読み込み

---

## 🔧 共通ユーティリティAPI

### KyoteiUtils

**ファイル**: `kyotei_predictor/utils/common.py`

#### クラス概要
競艇予測システムの共通ユーティリティクラス

#### 主要メソッド

##### `load_json_file(file_path: str) -> Dict[str, Any]`
JSONファイルを読み込み

##### `save_json_file(data: Dict[str, Any], file_path: str) -> bool`
JSONファイルに保存

##### `extract_race_result(race_data: Dict[str, Any]) -> Optional[Tuple[int, int, int]]`
レース結果（1着、2着、3着）を抽出

##### `calculate_expected_value(probability: float, odds: float) -> float`
期待値を計算

##### `is_profitable(expected_value: float, threshold: float = 1.0) -> bool`
投資価値があるか判定

##### `normalize_probabilities(probabilities: List[float]) -> List[float]`
確率を正規化（合計=1.0）

##### `softmax(x: List[float], temperature: float = 1.0) -> List[float]`
ソフトマックス関数

##### `get_ranking_distribution(predictions: List[Dict[str, Any]], actual_result: Tuple[int, int, int]) -> Dict[str, Any]`
予測結果の順位分布を計算

##### `calculate_hit_rates(results: List[Dict[str, Any]]) -> Dict[str, float]`
的中率を計算

##### `validate_race_data(race_data: Dict[str, Any]) -> bool`
レースデータの妥当性を検証

---

## 📈 分析ツールAPI

### TrifectaBulkValidator

**ファイル**: `kyotei_predictor/tools/analysis/trifecta_bulk_validator.py`

#### 機能概要
着順依存型3連単モデルによる大量データ検証

#### 主要関数

##### `bulk_validate(data_dir: str, max_races: int = 1000, output_dir: str = 'kyotei_predictor/outputs') -> Dict[str, Any]`
大量データでの検証を実行

**パラメータ:**
- `data_dir`: データディレクトリ
- `max_races`: 最大検証レース数
- `output_dir`: 出力ディレクトリ

**戻り値:**
```json
{
  "summary": {
    "total_races": 1000,
    "1st_hit_rate": 4.7,
    "top3_hit_rate": 11.8,
    "top5_hit_rate": 17.7,
    "top10_hit_rate": 32.4,
    "avg_rank": 31.24
  },
  "results": [...],
  "model_info": {...}
}
```

### RealOddsInvestmentAnalyzer

**ファイル**: `kyotei_predictor/tools/analysis/real_odds_investment_analyzer.py`

#### 機能概要
実際のオッズデータとモデル予測を組み合わせた投資価値分析

#### 主要関数

##### `analyze_investment_with_real_odds(data_dir: str, max_races: int = 100, output_dir: str = 'kyotei_predictor/outputs') -> Dict[str, Any]`
投資価値分析を実行

**パラメータ:**
- `data_dir`: データディレクトリ
- `max_races`: 最大分析レース数
- `output_dir`: 出力ディレクトリ

**戻り値:**
```json
{
  "summary": {
    "total_races": 50,
    "avg_investment_opportunities": 43.1,
    "total_opportunities": 2155,
    "hit_rate": 34.0
  },
  "results": [...],
  "investment_strategy": {...}
}
```

---

## ⚙️ 設定API

### Settings

**ファイル**: `kyotei_predictor/config/settings.py`

#### クラス概要
競艇予測システムの統合設定クラス

#### 主要設定項目

##### 基本設定
- `PROJECT_NAME`: プロジェクト名
- `VERSION`: バージョン

##### ディレクトリ設定
- `DATA_DIR`: データディレクトリ
- `OUTPUT_DIR`: 出力ディレクトリ
- `LOGS_DIR`: ログディレクトリ

##### Webアプリ設定
- `FLASK_HOST`: ホスト
- `FLASK_PORT`: ポート
- `FLASK_DEBUG`: デバッグモード

##### 予測モデル設定
- `TRIFECTA_COMBINATIONS`: 3連単組み合わせ数
- `DEFAULT_TEMPERATURE`: デフォルト温度
- `MIN_PROBABILITY`: 最小確率

##### 投資分析設定
- `DEFAULT_EXPECTED_VALUE_THRESHOLD`: デフォルト期待値閾値
- `CONSERVATIVE_THRESHOLD`: 保守的閾値
- `BALANCED_THRESHOLD`: バランス閾値
- `AGGRESSIVE_THRESHOLD`: 積極的閾値

#### 主要メソッド

##### `get_data_paths() -> Dict[str, str]`
データパスの辞書を取得

##### `get_web_config() -> Dict[str, Any]`
Webアプリ設定を取得

##### `get_model_config() -> Dict[str, Any]`
予測モデル設定を取得

##### `get_investment_config() -> Dict[str, float]`
投資分析設定を取得

##### `create_directories()`
必要なディレクトリを作成

---

## 🌐 WebアプリAPI

### Flaskアプリケーション

**ファイル**: `kyotei_predictor/app.py`

#### エンドポイント

##### `GET /`
メインページ

##### `GET /predict`
予測結果表示

##### `GET /analysis`
分析結果表示

##### `GET /investment`
投資分析結果表示

##### `POST /api/predict`
予測API

**リクエスト:**
```json
{
  "race_data": {...}
}
```

**レスポンス:**
```json
{
  "predictions": [...],
  "top_combination": "1-2-3",
  "top_probability": 0.125
}
```

##### `POST /api/analyze`
分析API

**リクエスト:**
```json
{
  "data_dir": "kyotei_predictor/data",
  "max_races": 1000
}
```

**レスポンス:**
```json
{
  "summary": {...},
  "results": [...]
}
```

---

## 📊 データ構造

### レースデータ構造

```json
{
  "race_id": "20250629_TSU_R1",
  "venue": "TSU",
  "race_number": 1,
  "date": "2025-06-29",
  "boats": [
    {
      "boat_number": 1,
      "course": 1,
      "age": 25,
      "weight": 52.5,
      "height": 165.2,
      "win_rate": 0.125,
      "place_rate": 0.375,
      "avg_start_time": 0.85,
      "motor_number": 1234,
      "boat_number_equipment": 5678,
      "arrival": 1
    }
  ]
}
```

### オッズデータ構造

```json
{
  "race_id": "20250629_TSU_R1",
  "trifecta_odds": {
    "1-2-3": 45.2,
    "1-2-4": 67.8,
    "1-2-5": 89.1
  }
}
```

### 予測結果構造

```json
{
  "combination": "1-2-3",
  "probability": 0.125,
  "rank": 1,
  "expected_value": 5.65
}
```

---

## 🔍 エラーハンドリング

### 共通エラーコード

- `1001`: データ読み込みエラー
- `1002`: データ検証エラー
- `2001`: モデル学習エラー
- `2002`: 予測計算エラー
- `3001`: ファイル保存エラー
- `3002`: ファイル読み込みエラー

### エラーレスポンス形式

```json
{
  "error": {
    "code": 1001,
    "message": "データ読み込みエラー",
    "details": "ファイルが見つかりません"
  }
}
```

---

## 📝 使用例

### 基本的な予測実行

```python
from kyotei_predictor.pipelines.trifecta_dependent_model import TrifectaDependentModel
from kyotei_predictor.utils.common import load_json

# モデル初期化
model = TrifectaDependentModel()

# 学習データで学習
model.learn_conditional_probabilities("kyotei_predictor/data", max_files=1000)

# レースデータ読み込み
race_data = load_json("race_data_20250629_TSU_R1.json")

# 予測実行
result = model.calculate_dependent_probabilities(race_data)
print(f"最適組み合わせ: {result['top_combination']}")
print(f"確率: {result['top_probability']:.3f}")
```

### 大量データ検証

```python
from kyotei_predictor.tools.analysis.trifecta_bulk_validator import bulk_validate

# 大量データ検証実行
result = bulk_validate(
    data_dir="kyotei_predictor/data",
    max_races=1000,
    output_dir="kyotei_predictor/outputs"
)

print(f"1位的中率: {result['summary']['1st_hit_rate']:.1f}%")
print(f"上位10位的中率: {result['summary']['top10_hit_rate']:.1f}%")
```

### 投資価値分析

```python
from kyotei_predictor.tools.analysis.real_odds_investment_analyzer import analyze_investment_with_real_odds

# 投資価値分析実行
result = analyze_investment_with_real_odds(
    data_dir="kyotei_predictor/data",
    max_races=50,
    output_dir="kyotei_predictor/outputs"
)

print(f"平均投資機会: {result['summary']['avg_investment_opportunities']:.1f}件/レース")
print(f"的中率: {result['summary']['hit_rate']:.1f}%")
```

---

## 🔄 バージョン履歴

### Phase 3 (2025-07-06)
- 着順依存型3連単モデルの実装
- 大量データ検証機能の追加
- 投資価値分析機能の追加
- 共通ユーティリティの統合

### Phase 2 (2025-07-03)
- パラメータ最適化機能の追加
- 特徴量拡張の実装

### Phase 1 (2025-07-01)
- 基本3連単予測アルゴリズムの実装
- データ取得機能の実装

---

**最終更新**: 2025-07-06  
**次回更新予定**: Phase 4完了時 