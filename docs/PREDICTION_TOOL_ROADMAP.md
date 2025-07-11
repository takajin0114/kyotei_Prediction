# 予想ツール運用ロードマップ

**最終更新日**: 2025-07-11  
**バージョン**: 1.2

---

## 📋 概要

本ドキュメントでは、kyotei_Predictionプロジェクトを**予想ツール**として運用するための方針と実装計画を記載します。

### 目標
- 深夜一括実行で前日データ取得・当日予測を自動化
- 全会場のレース予測を自動実行
- **3連単の予測確率を上位20組出力**
- **購入方法の提案機能を提供**
- 予測結果をJSON形式で保存・Web表示
- 運用負荷を最小化した完全自動化

---

## 🚀 実行フロー詳細

### 深夜一括実行フロー（例：7/12 02:00実行）

```
1. 前日データ取得・品質チェック
   ├── 7/11のレース結果データ取得
   ├── 7/11のオッズデータ取得
   ├── 欠損データの再取得
   └── データ品質チェック・レポート生成

2. 当日レース前データ取得
   ├── 7/12のレーススケジュール取得
   ├── 7/12の選手情報取得
   ├── 7/12のオッズ情報取得（レース前）
   └── レース前データの品質チェック

3. 予測実行
   ├── 学習済みモデルの読み込み
   ├── 特徴量エンジニアリング
   ├── 全会場・全レースの3連単予測実行
   └── 予測結果の検証

4. 結果保存・レポート生成
   ├── JSON形式で予測結果保存（上位20組）
   ├── 購入方法の提案生成
   ├── 実行ログ・履歴の記録
   └── エラー時のアラート通知
```

### 実行タイミング
- **深夜2時**: 一括実行（前日データ取得→当日予測）
- **実行時間**: 推定30-60分（全会場・全レース）
- **出力**: 朝9時までに予測結果が利用可能

---

## 📊 予測結果の形式・保存

### JSON形式（メイン）
```json
{
  "prediction_date": "2024-07-12",
  "generated_at": "2024-07-12T02:30:00",
  "model_info": {
    "model_name": "graduated_reward_best",
    "version": "2024-07-11",
    "training_data_until": "2024-07-11"
  },
  "execution_summary": {
    "total_venues": 24,
    "total_races": 48,
    "successful_predictions": 48,
    "execution_time_minutes": 15.5
  },
  "predictions": [
    {
      "venue": "KIRYU",
      "venue_code": "01",
      "race_number": 1,
      "race_time": "09:00",
      "top_20_combinations": [
        {
          "combination": "3-1-5",
          "probability": 0.085,
          "expected_value": 2.34,
          "rank": 1
        },
        {
          "combination": "3-1-2",
          "probability": 0.072,
          "expected_value": 1.98,
          "rank": 2
        },
        {
          "combination": "1-3-5",
          "probability": 0.068,
          "expected_value": 1.85,
          "rank": 3
        },
        {
          "combination": "3-5-1",
          "probability": 0.065,
          "expected_value": 1.72,
          "rank": 4
        },
        {
          "combination": "1-5-3",
          "probability": 0.062,
          "expected_value": 1.68,
          "rank": 5
        },
        {
          "combination": "5-3-1",
          "probability": 0.058,
          "expected_value": 1.55,
          "rank": 6
        },
        {
          "combination": "3-2-1",
          "probability": 0.055,
          "expected_value": 1.48,
          "rank": 7
        },
        {
          "combination": "2-3-1",
          "probability": 0.052,
          "expected_value": 1.42,
          "rank": 8
        },
        {
          "combination": "1-2-3",
          "probability": 0.049,
          "expected_value": 1.35,
          "rank": 9
        },
        {
          "combination": "2-1-3",
          "probability": 0.046,
          "expected_value": 1.28,
          "rank": 10
        },
        {
          "combination": "5-1-3",
          "probability": 0.043,
          "expected_value": 1.22,
          "rank": 11
        },
        {
          "combination": "1-3-2",
          "probability": 0.040,
          "expected_value": 1.15,
          "rank": 12
        },
        {
          "combination": "3-1-4",
          "probability": 0.037,
          "expected_value": 1.08,
          "rank": 13
        },
        {
          "combination": "4-3-1",
          "probability": 0.034,
          "expected_value": 1.02,
          "rank": 14
        },
        {
          "combination": "1-4-3",
          "probability": 0.031,
          "expected_value": 0.95,
          "rank": 15
        },
        {
          "combination": "3-4-1",
          "probability": 0.028,
          "expected_value": 0.88,
          "rank": 16
        },
        {
          "combination": "4-1-3",
          "probability": 0.025,
          "expected_value": 0.82,
          "rank": 17
        },
        {
          "combination": "2-5-3",
          "probability": 0.022,
          "expected_value": 0.75,
          "rank": 18
        },
        {
          "combination": "5-2-3",
          "probability": 0.019,
          "expected_value": 0.68,
          "rank": 19
        },
        {
          "combination": "3-2-5",
          "probability": 0.016,
          "expected_value": 0.61,
          "rank": 20
        }
      ],
      "total_probability": 0.892,
      "purchase_suggestions": [
        {
          "type": "nagashi",
          "description": "1-2-流し",
          "combinations": ["1-2-3", "1-2-4", "1-2-5", "1-2-6"],
          "total_probability": 0.156,
          "total_cost": 400,
          "expected_return": 624
        },
        {
          "type": "wheel",
          "description": "2-1-3 流し",
          "combinations": ["2-1-3", "2-1-4", "2-1-5", "2-1-6"],
          "total_probability": 0.142,
          "total_cost": 400,
          "expected_return": 568
        },
        {
          "type": "box",
          "description": "3-1-5 ボックス",
          "combinations": ["3-1-5", "3-5-1", "1-3-5", "1-5-3", "5-3-1", "5-1-3"],
          "total_probability": 0.393,
          "total_cost": 1200,
          "expected_return": 1176
        }
      ],
      "risk_level": "medium"
    }
  ],
  "venue_summaries": [
    {
      "venue": "KIRYU",
      "total_races": 12,
      "high_confidence_races": 3,
      "average_top_probability": 0.085,
      "average_expected_value": 1.85
    }
  ]
}
```

### 購入方法の提案ロジック

#### 1. 流し買い（Nagashi）
- 同じ1-2着の組み合わせで3着を流す
- 例: 1-2-3, 1-2-4, 1-2-5, 1-2-6 → "1-2-流し"

#### 2. 流し買い（Wheel）
- 同じ1着で2-3着を流す
- 例: 2-1-3, 2-1-4, 2-1-5, 2-1-6 → "2-1-流し"

#### 3. ボックス買い（Box）
- 上位組み合わせの順列を全て含む
- 例: 3-1-5, 3-5-1, 1-3-5, 1-5-3, 5-3-1, 5-1-3 → "3-1-5 ボックス"

#### 4. 単勝買い（Single）
- 上位1-3組の単勝買い
- 例: "3-1-5", "3-1-2", "1-3-5"

### ファイル保存構造
```
outputs/
├── predictions_2024-07-12.json    # 日付別予測結果
├── predictions_2024-07-11.json    # 前日分
├── predictions_latest.json        # 最新分（シンボリックリンク）
└── prediction_history.json        # 実行履歴
```

---

## 🌐 Web表示の仕組み

### 実装方針
- **静的HTML + JavaScript**で実装
- JSONファイルを直接読み込んで表示
- ソート・フィルタ機能付き
- **購入方法の提案表示機能**

### 表示機能
- 全会場の予測結果一覧
- 会場別・レース別の詳細表示
- **3連単上位20組の確率表示**
- **購入方法の提案表示**
- 期待値・信頼度でのソート
- 高信頼度レースのハイライト

### 技術構成
```html
<!-- predictions.html -->
<!DOCTYPE html>
<html>
<head>
    <title>競艇予測結果</title>
</head>
<body>
    <div id="predictions"></div>
    
    <script>
        // JSONファイルを読み込んで表示
        fetch('/outputs/predictions_latest.json')
            .then(response => response.json())
            .then(data => {
                displayPredictions(data);
            });
        
        function displayPredictions(data) {
            // 予測結果をテーブル形式で表示
            // 3連単上位20組の確率表示
            // 購入方法の提案表示
            // ソート・フィルタ機能付き
        }
        
        function displayPurchaseSuggestions(suggestions) {
            // 購入方法の提案を表示
            // 流し、ボックス、単勝の各タイプを分けて表示
        }
    </script>
</body>
</html>
```

---

## 🛠️ 実装計画

### Phase 1: ラッパースクリプト拡張（1-2週間）
- [ ] レース前データ取得機能の追加
- [ ] **3連単予測実行機能の追加**
- [ ] **上位20組の確率計算機能の追加**
- [ ] **購入方法の提案生成機能の追加**
- [ ] JSON保存機能の追加
- [ ] 実行フローの統合

### Phase 2: Web表示実装（1週間）
- [ ] 静的HTMLファイルの作成
- [ ] JavaScriptでのJSON読み込み・表示
- [ ] **3連単上位20組の表示機能**
- [ ] **購入方法の提案表示機能**
- [ ] 基本的なソート・フィルタ機能
- [ ] レスポンシブデザイン対応

### Phase 3: 運用開始・改善（継続）
- [ ] 深夜スケジューラでの自動実行
- [ ] 予測精度の監視・改善
- [ ] ユーザーフィードバック対応

---

## 📋 技術要件

### 必要な機能
1. **レース前データ取得**
   - 当日のレーススケジュール
   - 選手情報・オッズ情報
   - 天候・コース条件

2. **予測実行**
   - 学習済みモデルの読み込み
   - 特徴量エンジニアリング
   - **全会場・全レースの3連単予測**
   - **上位20組の確率計算**

3. **購入方法提案**
   - **流し買いの自動提案**
   - **ボックス買いの自動提案**
   - **単勝買いの自動提案**
   - **期待値・コスト計算**

4. **結果保存・表示**
   - JSON形式での保存
   - Web表示機能
   - 履歴管理

### 運用要件
- 深夜自動実行
- エラー時のアラート通知
- 実行ログ・履歴の管理
- 予測精度の継続監視

---

## 🎯 成功指標

### 技術指標
- 実行成功率: 99%以上
- 予測実行時間: 60分以内
- データ取得成功率: 99%以上
- **3連単予測精度: 上位20組の的中率**
- **購入方法提案の精度**

### 運用指標
- 朝9時までに予測結果が利用可能
- Web表示の応答時間: 3秒以内
- ユーザー満足度の向上

---

## 📚 関連ドキュメント

- [SCHEDULED_MAINTENANCE_GUIDE.md](SCHEDULED_MAINTENANCE_GUIDE.md) - スケジューラ化運用ガイド
- [data_acquisition.md](data_acquisition.md) - データ取得運用
- [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) - 全体開発計画

---

## 📝 更新履歴

- **2025-07-11**: 購入方法の提案機能を追加、高信頼度組み合わせ・推奨買い目を削除
- **2025-07-11**: 3連単予測確率上位20組出力形式に変更
- **2025-07-11**: 初版作成、予想ツール運用方針策定 