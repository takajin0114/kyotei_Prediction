# pipelines ディレクトリ README

**最終更新日: 2025-07-04**

---

## 本READMEの役割
- データ前処理・特徴量生成・AI学習環境などパイプラインの役割・使い方を記載
- 典型的な処理フロー・設計書へのリンクを明記
- ルートREADMEやNEXT_STEPS.mdへのリンクも記載

## 関連ドキュメント
- [../../README.md](../../README.md)（全体概要・セットアップ・タスク入口）
- [../../NEXT_STEPS.md](../../NEXT_STEPS.md)（今後のタスク・優先度・進捗管理）
- [../../integration_design.md](../../integration_design.md)（統合設計・アーキテクチャ）
- [../../prediction_algorithm_design.md](../../prediction_algorithm_design.md)（予測アルゴリズム設計）

---

## 構成・機能分割方針
- 前処理（data_preprocessor.py）・特徴量生成（feature_enhancer.py）・AI学習環境（kyotei_env.py）など、用途別にスクリプトを整理
- 今後は「データ検証」「パイプライン自動化」「追加特徴量」なども用途別に追加
- 共通処理は tools/common/ へ集約

---

## 📁 主なスクリプト
- `data_preprocessor.py` : データ前処理・クリーニング
- `feature_enhancer.py` : 特徴量エンジニアリング
- `kyotei_env.py` : 強化学習用環境クラス

---

## 📝 サンプル処理フロー
```python
# 1. 生データの前処理
from pipelines.data_preprocessor import preprocess_raw_data
cleaned = preprocess_raw_data('data/raw/race_data_20250701_KIRYU_R1.json')

# 2. 特徴量エンジニアリング
from pipelines.feature_enhancer import add_features
featured = add_features(cleaned)

# 3. AI学習環境の構築
from pipelines.kyotei_env import KyoteiEnv
env = KyoteiEnv(featured)
```

---

## 運用方針
- データ取得後、raw/→processed/への変換処理を担当
- AI学習・推論用のデータセット生成
- 新規パイプラインは本ディレクトリに追加
- 共通処理は tools/common/ へ集約

---

## 備考
- 中間生成物は data/processed/ へ保存
- パイプラインの自動化は今後 scripts/ や workflow/ で管理予定
- テストコードは tests/ 配下に設置
- 用途別にスクリプトを整理し、READMEも随時更新

---

## 3連単確率計算パイプライン（B-1対応）
- 予測アルゴリズムで算出した各艇のスコアから、全120通りの3連単組み合わせの確率を計算
- `kyotei_predictor/pipelines/trifecta_probability.py` の `TrifectaProbabilityCalculator` クラスを利用
- 既存の `kyotei_predictor/prediction_engine.py` の `calculate_trifecta_probabilities`・`get_top_trifecta_recommendations` も利用可能
- テスト例: `tests/ai/test_trifecta_probability.py` で自動検証・オッズ比較も可能

### サンプルフロー（直接利用）
```python
from kyotei_predictor.pipelines.trifecta_probability import TrifectaProbabilityCalculator
# 各艇の予測スコア・勝率リスト（例）
predictions = [
    {'pit_number': 1, 'win_probability': 30.0},
    {'pit_number': 2, 'win_probability': 20.0},
    {'pit_number': 3, 'win_probability': 18.0},
    {'pit_number': 4, 'win_probability': 12.0},
    {'pit_number': 5, 'win_probability': 10.0},
    {'pit_number': 6, 'win_probability': 10.0},
]
calculator = TrifectaProbabilityCalculator()
trifecta_probs = calculator.calculate(predictions)
for combo in trifecta_probs[:5]:
    print(combo)
```

### サンプルフロー（PredictionEngine経由）
```python
from kyotei_predictor.prediction_engine import PredictionEngine
engine = PredictionEngine()
# race_data: 予測用データ（dict形式）
trifecta_probs = engine.calculate_trifecta_probabilities(predictions)
# または
result = engine.get_top_trifecta_recommendations(race_data, algorithm='comprehensive', top_n=10)
print(result['top_combinations'])
```
- サンプルデータ: `data/raw/complete_race_data_*.json` など
- 実際のオッズ比較: `odds_data_*.json` も活用可 

### サンプルフロー（コース特性・オッズ補正込み）
```python
from kyotei_predictor.pipelines.trifecta_probability import TrifectaProbabilityCalculator
# コース特性・オッズ補正を含むサンプルデータ
predictions = [
    {'pit_number': 1, 'rate_in_all_stadium': 6.5, 'rate_in_event_going_stadium': 7.0, 'current_rating': 'A1', 'boat_quinella_rate': 44.0, 'motor_quinella_rate': 38.0, 'course_bias': 0.5, 'odds_bias': 0.1},
    {'pit_number': 2, 'rate_in_all_stadium': 5.8, 'rate_in_event_going_stadium': 6.2, 'current_rating': 'A2', 'boat_quinella_rate': 41.0, 'motor_quinella_rate': 35.0, 'course_bias': 0.3, 'odds_bias': 0.2},
    {'pit_number': 3, 'rate_in_all_stadium': 5.2, 'rate_in_event_going_stadium': 5.5, 'current_rating': 'B1', 'boat_quinella_rate': 38.0, 'motor_quinella_rate': 32.0, 'course_bias': 0.2, 'odds_bias': 0.3},
    {'pit_number': 4, 'rate_in_all_stadium': 4.9, 'rate_in_event_going_stadium': 5.0, 'current_rating': 'B1', 'boat_quinella_rate': 36.0, 'motor_quinella_rate': 30.0, 'course_bias': 0.1, 'odds_bias': 0.4},
    {'pit_number': 5, 'rate_in_all_stadium': 4.5, 'rate_in_event_going_stadium': 4.8, 'current_rating': 'B2', 'boat_quinella_rate': 33.0, 'motor_quinella_rate': 28.0, 'course_bias': 0.0, 'odds_bias': 0.5},
    {'pit_number': 6, 'rate_in_all_stadium': 4.2, 'rate_in_event_going_stadium': 4.5, 'current_rating': 'B2', 'boat_quinella_rate': 30.0, 'motor_quinella_rate': 25.0, 'course_bias': -0.1, 'odds_bias': 0.6},
]
weights = {
    'all_stadium_rate': 0.2,
    'event_going_rate': 0.2,
    'rating': 0.1,
    'boat_quinella_rate': 0.2,
    'motor_quinella_rate': 0.2,
    'course_bias': 0.15,
    'odds_bias': 0.15,
}
calculator = TrifectaProbabilityCalculator(weights=weights)
trifecta_probs = calculator.calculate(predictions)
for combo in trifecta_probs[:5]:
    print(combo)
```

---

## 機材重視アルゴリズムパイプライン（B-2対応）
- ボート・モーター成績を重視した予測（equipment_focusedアルゴリズム）
- `kyotei_predictor/prediction_engine.py` の `predict(..., algorithm='equipment_focused')` を利用
- テスト例: `tests/ai/test_phase2_algorithms.py` で自動検証・特徴分析も可能

### サンプルフロー
```python
from kyotei_predictor.prediction_engine import PredictionEngine
engine = PredictionEngine()
# race_data: 予測用データ（dict形式）
result = engine.predict(race_data, algorithm='equipment_focused')
print(result['predictions'])
```
- サンプルデータ: `data/raw/complete_race_data_*.json` など
- 他アルゴリズムとの比較: `test_phase2_algorithms.py` で一括検証可 

---

## 選手の調子・競艇場特性・リアルタイムオッズ考慮パイプライン（B-3対応）
- 直近成績（recent_form）、会場特性（venue_bias）、リアルタイムオッズ（popularity, odds_data）を特徴量・補正値としてスコアに加算
- `pipelines/feature_enhancer.py` でrecent_form等の特徴量生成例あり
- `tools/fetch/odds_fetcher.py` でオッズデータ取得、`tools/analysis/odds_analysis.py` でオッズ比較分析
- PredictionEngineで補正ロジック追加・テストで検証可能

### サンプルフロー
```python
from kyotei_predictor.pipelines.feature_enhancer import FeatureEnhancer
from kyotei_predictor.prediction_engine import PredictionEngine
# DataFrameにrecent_form等の特徴量を追加
enhancer = FeatureEnhancer()
df = enhancer.enhance(df, auto_correct=True)
# PredictionEngineで補正ロジックを追加して予測
engine = PredictionEngine()
result = engine.predict(race_data, algorithm='comprehensive', options={'use_recent_form': True, 'use_venue_bias': True, 'use_odds': True})
print(result['predictions'])
```
- サンプルデータ: `data/raw/complete_race_data_*.json`, `odds_data_*.json` など
- 拡張例: pipelines/feature_enhancer.pyで特徴量追加、PredictionEngineで補正ロジック拡張 

---

## データベース連携パイプライン（B-4対応・拡張）
- 複数レースデータの一括インポート: `import_race_json_bulk(directory, db)`
- 全レース一覧取得: `db.fetch_all_races()`
- 特定レースの着順・タイム取得: `db.fetch_results_by_race(race_id)`

### サンプルフロー
```python
from kyotei_predictor.pipelines.db_integration import KyoteiDB, import_race_json_bulk
# DB作成・一括インポート
with KyoteiDB() as db:
    import_race_json_bulk('kyotei_predictor/data/raw', db)
    all_races = db.fetch_all_races()
    print(f"登録レース数: {len(all_races)}")
    results = db.fetch_results_by_race('2024-06-06_KIRYU_R1')
    for r in results:
        print(r)
```
- 運用方針: サンプルデータ→DB一元化→Webアプリ・分析・学習で再利用
- 今後: テーブル拡張（選手・機材・オッズ等）、クエリAPI拡張、運用ルールは設計書にも反映 

---

## 統計分析・可視化パイプライン（B-5対応）
- DBからコース別勝率・平均タイムなどの統計を集計
- `tools/analysis/race_stats.py` の `calc_course_win_rate`, `calc_course_avg_time`, `plot_course_stats` を利用

### サンプルフロー
```python
from kyotei_predictor.pipelines.db_integration import KyoteiDB
from kyotei_predictor.tools.analysis.race_stats import calc_course_win_rate, calc_course_avg_time, plot_course_stats
with KyoteiDB() as db:
    print('コース別勝率:', calc_course_win_rate(db))
    print('コース別平均タイム:', calc_course_avg_time(db))
    plot_course_stats(db)
```
- 運用方針: DB一元化データを活用し、分析・可視化・レポート作成に応用
- 今後: 選手・機材・オッズ等の分析指標・可視化も拡張予定 