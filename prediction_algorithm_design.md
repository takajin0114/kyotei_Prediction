# 競艇予測アルゴリズム設計書

## 📋 概要

競艇予測Webアプリケーションにおける予測アルゴリズムの設計仕様書。
段階的な実装により、基本的な勝率ベース予測から高度な機械学習アプローチまでを実現する。

**作成日**: 2025-06-13  
**バージョン**: 1.0  
**対象レース**: 競艇（ボートレース）6艇立て

---

## 📊 利用可能データ分析

### 1. 選手データ
| データ項目 | 型 | 範囲例 | 説明 |
|-----------|----|---------|----|
| `rate_in_all_stadium` | float | 3.89〜5.75 | 全国勝率 |
| `rate_in_event_going_stadium` | float | 3.00〜7.11 | 当地勝率 |
| `current_rating` | string | A1, A2, B1, B2 | 級別 |
| `registration_number` | int | 3741〜4740 | 選手登録番号 |
| `name` | string | "北川 太一" | 選手名 |

### 2. 機材データ
| データ項目 | 型 | 範囲例 | 説明 |
|-----------|----|---------|----|
| `boat.quinella_rate` | float | 23.85〜44.57 | ボート2連率(%) |
| `boat.trio_rate` | float | 43.12〜57.61 | ボート3連率(%) |
| `motor.quinella_rate` | float | 28.09〜40.0 | モーター2連率(%) |
| `motor.trio_rate` | float | 47.19〜61.73 | モーター3連率(%) |
| `boat.number` | int | 13〜75 | ボート番号 |
| `motor.number` | int | 13〜75 | モーター番号 |

### 3. レース条件
| データ項目 | 型 | 値例 | 説明 |
|-----------|----|---------|----|
| `weather` | string | FINE, CLOUDY, RAIN | 天候 |
| `wind_velocity` | float | 0.0〜10.0 | 風速(m/s) |
| `wind_angle` | float | 0.0〜360.0 | 風向(度) |
| `air_temperature` | float | 10.0〜35.0 | 気温(℃) |
| `water_temperature` | float | 5.0〜30.0 | 水温(℃) |
| `wavelength` | float | 0.0〜10.0 | 波高(cm) |

### 4. 検証用データ
| データ項目 | 型 | 値例 | 説明 |
|-----------|----|---------|----|
| `arrival` | int | 1〜6 | 実際の着順 |
| `start_time` | float | 0.12〜0.22 | スタートタイム(秒) |
| `total_time` | float | 112.0〜118.1 | 総タイム(秒) |
| `winning_trick` | string | MAKURI, SASHI, NIGE | 決まり手 |

---

## 🧮 アルゴリズム設計

### レベル1: 基本アルゴリズム 🔥 **P0**

#### 1-1. シンプル勝率ベース
**目的**: 最もシンプルな予測の実現  
**実装優先度**: 最高

```python
基本スコア = 全国勝率 × 0.6 + 当地勝率 × 0.4
```

**特徴**:
- ✅ 実装が簡単（15分で実装可能）
- ✅ 理解しやすい
- ✅ 即座に結果が出る
- ❌ 他の要素を考慮しない
- ❌ 精度は限定的

**適用場面**: 初期実装、動作確認、ベースライン

#### 1-2. 級別重み付け
**目的**: 選手の実力差を反映した予測

```python
級別係数 = {
    'A1': 1.2,  # A1級（最上位）
    'A2': 1.1,  # A2級（上位）
    'B1': 1.0,  # B1級（標準）
    'B2': 0.9   # B2級（下位）
}

級別補正スコア = (全国勝率 × 0.6 + 当地勝率 × 0.4) × 級別係数
```

**特徴**:
- ✅ 級別の実力差を反映
- ✅ 基本アルゴリズムの自然な拡張
- ✅ 理解しやすい重み付け

**適用場面**: 基本予測の改良版

---

### レベル2: 中級アルゴリズム ⚡ **P1**

#### 2-1. 総合評価アルゴリズム
**目的**: 選手・機材の総合的な評価

```python
選手スコア = 全国勝率 × 0.35 + 当地勝率 × 0.25 + 級別補正 × 0.1
機材スコア = ボート2連率 × 0.15 + モーター2連率 × 0.15

総合スコア = 選手スコア + 機材スコア
```

**重み配分の根拠**:
- **全国勝率 35%**: 選手の基本実力
- **当地勝率 25%**: 競艇場適性
- **級別補正 10%**: 公式実力認定
- **ボート成績 15%**: 機材の影響
- **モーター成績 15%**: エンジン性能

**特徴**:
- ✅ 多角的な評価
- ✅ 機材の影響を考慮
- ✅ バランスの取れた重み配分
- ❌ 天候・コース条件は未考慮

#### 2-2. 機材重視アルゴリズム
**目的**: ボート・モーター成績を重視した評価

```python
選手スコア = 全国勝率 × 0.4 + 当地勝率 × 0.3 + 級別補正 × 0.1
機材スコア = (ボート2連率 × 0.1 + モーター2連率 × 0.1) / 100

# 機材成績を重視した総合評価
機材重視スコア = 選手スコア + 機材スコア

# 機材ボーナス（特に良い機材の場合）
if ボート2連率 > 40 or モーター2連率 > 35:
    機材ボーナス = 0.1
else:
    機材ボーナス = 0

最終スコア = 機材重視スコア + 機材ボーナス
```

**特徴**:
- ✅ 機材成績の影響を明確に評価
- ✅ 高性能機材のボーナス評価
- ✅ 事前に取得可能なデータのみ使用

#### 2-3. 3連単確率計算アルゴリズム
**目的**: 各艇のスコアから3連単の確率を算出し、投資判断を支援

```python
def calculate_trifecta_probabilities(individual_scores):
    """
    各艇のスコアから3連単の確率を計算
    
    Args:
        individual_scores: 各艇の予測スコア [score1, score2, ..., score6]
    
    Returns:
        trifecta_probabilities: 3連単の確率辞書
    """
    
    # 1. 各艇の勝率を正規化
    win_probabilities = normalize_to_probabilities(individual_scores)
    
    # 2. 3連単の全組み合わせ (6P3 = 120通り)
    trifecta_combinations = generate_trifecta_combinations()
    
    # 3. 各組み合わせの確率を計算
    trifecta_probs = {}
    for combo in trifecta_combinations:
        # 1着確率 × 2着確率 × 3着確率
        prob = (win_probabilities[combo[0]-1] * 
                win_probabilities[combo[1]-1] * 
                win_probabilities[combo[2]-1])
        trifecta_probs[f"{combo[0]}-{combo[1]}-{combo[2]}"] = prob
    
    return trifecta_probs
```

**特徴**:
- ✅ 120通りの3連単組み合わせを網羅
- ✅ オッズとの比較による投資価値分析
- ✅ 実際の舟券購入判断に直結

---

### レベル3: 高級アルゴリズム 📈 **P2**

#### 3-1. 機械学習風アプローチ
**目的**: 過去データからの学習による高精度予測

```python
# 特徴量エンジニアリング
特徴量ベクトル = [
    # 選手関連
    全国勝率, 当地勝率, 級別数値化,
    
    # 機材関連
    ボート2連率, ボート3連率,
    モーター2連率, モーター3連率,
    
    # 環境関連（将来拡張用）
    # 注意: 環境データはレース当日まで確定しないため現在は未使用
    
    # 相対評価
    勝率ランキング, 機材ランキング,
    
    # 派生特徴量
    勝率差分, 機材総合評価,
    天候適性スコア
]

# 重み学習（過去データから最適化）
重み配列 = 過去データから学習された最適重み

予測スコア = Σ(特徴量[i] × 重み[i]) + バイアス項
```

**特徴量設計**:
- **正規化**: 全特徴量を0-1範囲に正規化
- **相対評価**: 他艇との相対的な強さを数値化
- **派生特徴量**: 既存データから計算される新しい指標

#### 3-2. 相対評価アルゴリズム
**目的**: 各艇の相対的な強さに基づく予測

```python
def calculate_relative_strength(race_entries):
    relative_scores = []
    
    for target_boat in race_entries:
        wins = 0
        total_comparisons = 0
        
        for other_boat in race_entries:
            if target_boat != other_boat:
                # 各要素での比較
                if target_boat.all_stadium_rate > other_boat.all_stadium_rate:
                    wins += 1
                if target_boat.local_rate > other_boat.local_rate:
                    wins += 1
                if target_boat.boat_rate > other_boat.boat_rate:
                    wins += 1
                if target_boat.motor_rate > other_boat.motor_rate:
                    wins += 1
                
                total_comparisons += 4
        
        relative_strength = wins / total_comparisons
        relative_scores.append(relative_strength)
    
    return relative_scores
```

#### 3-3. 投資価値分析アルゴリズム
**目的**: 3連単の確率とオッズを比較し、投資価値を算出

```python
def calculate_investment_value(trifecta_probabilities, odds_data):
    """
    3連単の予測確率とオッズから投資価値を分析
    
    Args:
        trifecta_probabilities: 予測した3連単確率
        odds_data: 実際のオッズ情報
    
    Returns:
        investment_analysis: 投資価値分析結果
    """
    
    investment_opportunities = []
    
    for combination, predicted_prob in trifecta_probabilities.items():
        if combination in odds_data:
            odds = odds_data[combination]
            expected_return = odds * predicted_prob
            
            # 期待値が1.0を超える場合は投資価値あり
            if expected_return > 1.2:  # 20%以上の期待利益
                investment_opportunities.append({
                    'combination': combination,
                    'predicted_probability': predicted_prob,
                    'odds': odds,
                    'expected_return': expected_return,
                    'investment_value': 'high' if expected_return > 1.5 else 'medium'
                })
    
    return sorted(investment_opportunities, 
                 key=lambda x: x['expected_return'], reverse=True)
```

**特徴**:
- ✅ 期待値理論に基づく投資判断
- ✅ リスク・リターンの定量評価
- ✅ 実際の舟券購入戦略に直結


---

## 🎯 実装計画

### Phase 1: 基本実装 (タスク3 - 75分)
| 項目 | 所要時間 | 内容 |
|------|----------|------|
| シンプル勝率ベース | 15分 | 基本的な勝率計算 |
| 級別重み付け | 15分 | 級別係数の適用 |
| PredictionEngineクラス | 30分 | 基本クラス設計・実装 |
| 動作確認・テスト | 15分 | サンプルデータでの検証 |

### Phase 2: 中級実装 (タスク4 - 90分)
| 項目 | 所要時間 | 内容 |
|------|----------|------|
| 総合評価アルゴリズム | 30分 | 選手・機材の総合評価 |
| 機材重視アルゴリズム | 20分 | ボート・モーター成績重視 |
| 3連単確率計算 | 40分 | 120通りの組み合わせ確率算出 |

### Phase 3: 高級実装 (将来拡張)
| 項目 | 所要時間 | 内容 |
|------|----------|------|
| 機械学習アプローチ | 120分 | 特徴量エンジニアリング（環境データ除く） |
| 相対評価アルゴリズム | 60分 | 他艇との比較による強さ評価 |
| 投資価値分析 | 90分 | オッズ比較・期待値計算 |

---

## 🧪 検証・評価方法

### 1. サンプルデータ検証
**対象レース**: 2024年6月15日 桐生競艇場 第1レース

**実際の結果**:
```
1着: 3号艇 松尾基成 (B1級, 全国勝率4.07, 当地勝率4.22)
2着: 5号艇 北川太一 (A2級, 全国勝率5.75, 当地勝率7.11)
3着: 6号艇 上之晃弘 (A2級, 全国勝率4.89, 当地勝率5.20)
```

**検証項目**:
- 各アルゴリズムの1着予測
- スコア順位と実際の着順の相関
- A級選手の評価が適切か

### 2. 予測精度指標

#### 2-1. 的中率指標
```python
的中率 = 正解予測数 / 総予測数

# 段階別評価
単勝的中率 = 1着予測の正解率
連対的中率 = 1-2着予測の正解率  
3連対的中率 = 1-2-3着予測の正解率
```

#### 2-2. スコア妥当性
```python
# 相関係数による評価
相関係数 = correlation(予測スコア順位, 実際の着順)

# 期待値: 0.6以上で良好、0.8以上で優秀
```

#### 2-3. アルゴリズム比較
```python
比較指標 = {
    'accuracy': 的中率,
    'correlation': 相関係数,
    'score_range': スコア分布の適切性,
    'computation_time': 計算時間,
    'interpretability': 解釈しやすさ
}
```

### 3. 妥当性チェック

#### 3-1. 基本妥当性
- [ ] 高勝率選手が高スコアになる
- [ ] A級選手がB級選手より高スコア
- [ ] 当地勝率の高い選手が有利に評価される
- [ ] 機材成績の良い組み合わせが高評価

#### 3-2. 機材別妥当性
- [ ] 高性能ボートの選手が高評価される
- [ ] 高性能モーターの選手が高評価される
- [ ] 機材ボーナスが適切に適用される
- [ ] 機材成績の差が予測に反映される

#### 3-3. 極端値チェック
- [ ] スコアが負の値にならない
- [ ] スコアが異常に高い値にならない
- [ ] 全艇のスコアが同じ値にならない
- [ ] 明らかに弱い選手が1位予測にならない

---

## 📋 実装仕様

### クラス設計
```python
class PredictionEngine:
    """競艇予測エンジンのメインクラス"""
    
    def __init__(self):
        self.algorithms = {
            'basic': self.basic_algorithm,
            'rating_weighted': self.rating_weighted_algorithm,
            'comprehensive': self.comprehensive_algorithm,
            'equipment_focused': self.equipment_focused_algorithm,
            'ml_approach': self.ml_approach_algorithm,
            'relative_evaluation': self.relative_evaluation_algorithm
        }
        
        self.weights = self._load_algorithm_weights()
        self.coefficients = self._load_correction_coefficients()
    
    def predict(self, race_data, algorithm='basic', options=None):
        """予測実行のメインメソッド"""
        pass
    
    def _validate_race_data(self, race_data):
        """レースデータの検証"""
        pass
    
    def _normalize_scores(self, scores):
        """スコアの正規化"""
        pass
    
    def _calculate_win_probabilities(self, scores):
        """勝率の計算"""
        pass
```

### 出力形式
```json
{
  "algorithm": "comprehensive",
  "execution_time": 0.045,
  "race_info": {
    "date": "2024-06-15",
    "stadium": "KIRYU",
    "race_number": 1,
    "weather": "FINE",
    "wind_velocity": 4.0,
    "total_boats": 6
  },
  "predictions": [
    {
      "rank": 1,
      "pit_number": 5,
      "racer_name": "北川 太一",
      "rating": "A2",
      "prediction_score": 5.85,
      "win_probability": 28.5,
      "confidence": "high",
      "details": {
        "base_score": 5.75,
        "racer_component": 5.2,
        "boat_component": 0.3,
        "motor_component": 0.25,
        "weather_factor": 1.0,
        "course_factor": 0.9,
        "adjustments": {
          "rating_bonus": 0.1,
          "local_bonus": 0.15,
          "weather_penalty": 0.0
        }
      }
    }
  ],
  "summary": {
    "favorite": {
      "pit_number": 5,
      "racer_name": "北川 太一",
      "win_probability": 28.5
    },
    "dark_horse": {
      "pit_number": 3,
      "racer_name": "松尾 基成",
      "win_probability": 18.2
    },
    "score_distribution": {
      "max": 5.85,
      "min": 3.45,
      "average": 4.65,
      "std_dev": 0.89
    },
    "confidence_level": "medium"
  },
  "validation": {
    "data_quality": "good",
    "missing_fields": [],
    "warnings": [],
    "recommendation": "予測結果は信頼できます"
  }
}
```

### エラーハンドリング
```python
class PredictionError(Exception):
    """予測エラーの基底クラス"""
    pass

class DataValidationError(PredictionError):
    """データ検証エラー"""
    pass

class AlgorithmError(PredictionError):
    """アルゴリズム実行エラー"""
    pass

class ConfigurationError(PredictionError):
    """設定エラー"""
    pass
```

---

## 🔄 将来の拡張計画

### 短期拡張 (1-2ヶ月)
- [ ] 過去レース結果の蓄積・分析
- [ ] 選手の調子（最近の成績）の考慮
- [ ] 競艇場別の特性データ追加
- [ ] リアルタイムオッズ情報の活用

### 中期拡張 (3-6ヶ月)
- [ ] 機械学習モデルの本格導入
- [ ] 大量データによる重み最適化
- [ ] 選手間の相性・対戦成績分析
- [ ] 季節・時間帯による補正

### 長期拡張 (6ヶ月以上)
- [ ] ディープラーニングによる予測
- [ ] リアルタイム学習・重み更新
- [ ] 複数競艇場の横断分析
- [ ] 予測精度の自動評価・改善

---

## 📚 参考資料

### 競艇の基礎知識
- **級別制度**: A1(上位) > A2 > B1 > B2(下位)
- **コース有利性**: 1コース(イン) > 2コース > ... > 6コース(アウト)
- **決まり手**: NIGE(逃げ), SASHI(差し), MAKURI(まくり)等

### 統計データ
- **1コース勝率**: 約50-55%
- **6コース勝率**: 約5-8%
- **A1級平均勝率**: 約6.5-7.5
- **B2級平均勝率**: 約3.5-4.5

### 技術参考
- **正規化手法**: Min-Max正規化、Z-score正規化
- **重み最適化**: 最小二乗法、勾配降下法
- **相関分析**: ピアソン相関係数、スピアマン順位相関

---

**最終更新**: 2025-06-13  
**次回更新予定**: 実装完了後  
**レビュー**: 実装前・実装後・運用開始後に実施