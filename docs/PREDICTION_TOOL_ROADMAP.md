# 予想ツール運用ロードマップ

**最終更新日**: 2025-07-13  
**バージョン**: 2.0

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
      "purchase_suggestions": [
        {
          "type": "nagashi",
          "description": "流し買い",
          "combinations": ["3-1-5", "3-1-2", "1-3-5"],
          "total_cost": 300,
          "expected_return": 625.5,
          "expected_profit": 325.5,
          "risk_level": "medium"
        },
        {
          "type": "box",
          "description": "ボックス買い",
          "combinations": ["3-1-5", "3-5-1", "1-3-5", "1-5-3", "5-3-1"],
          "total_cost": 600,
          "expected_return": 1020.0,
          "expected_profit": 420.0,
          "risk_level": "high"
        },
        {
          "type": "tansho",
          "description": "単勝買い",
          "combinations": ["3"],
          "total_cost": 100,
          "expected_return": 150.0,
          "expected_profit": 50.0,
          "risk_level": "low"
        }
      ]
    }
  ]
}
```

### 購入方法の提案形式
各レースに対して、以下の3つの購入方法を提案：

1. **流し買い（nagashi）**
   - 上位3組の組み合わせを流し買い
   - 中程度のリスク、安定した期待値

2. **ボックス買い（box）**
   - 上位5組の組み合わせをボックス買い
   - 高リスク、高期待値

3. **単勝買い（tansho）**
   - 最も確率の高い1着を単勝買い
   - 低リスク、低期待値

---

## 🎯 実装状況

### ✅ 完了済み（2025-07-13時点）
- **統合実行フロー**: `run_complete_prediction()`メソッドの実装完了
- **3連単予測機能**: 上位20組の確率計算・出力機能実装完了
- **購入方法提案機能**: 流し・ボックス・単勝買いの自動提案機能実装完了
- **JSON保存機能**: 予測結果のJSON形式保存機能実装完了
- **会場フィルタリング**: 特定会場のみの予測実行機能実装完了
- **状態ベクトル修正**: 192次元の正確な状態ベクトル生成実装完了
- **テスト成功**: TAMAGAWA会場12レースでの予測成功確認

### 🔄 進行中
- **Web表示機能実装**: 静的HTMLファイルでの予測結果表示機能を実装中

### 📋 計画中・実装待ち
- **深夜自動実行開始**: スケジューラ設定、エラー処理・アラート機能
- **運用監視システム**: 実行状況の監視、エラー検知・復旧

---

## 🛠️ 技術実装詳細

### 予想ツールの主要機能
```python
class PredictionTool:
    def run_complete_prediction(self, target_date: str = None, venues: List[str] = None) -> Dict:
        """完全統合予測フロー"""
        # 1. 当日レーススケジュール取得
        # 2. 当日選手情報取得
        # 3. 当日オッズ情報取得
        # 4. 3連単予測実行
        # 5. 購入方法提案生成
        # 6. 結果保存

    def predict_trifecta_probabilities(self, race_data: Dict, odds_data: Dict) -> List[Dict]:
        """3連単予測"""
        # 192次元状態ベクトル生成
        # PPOモデルによる予測
        # 上位20組の確率計算

    def generate_purchase_suggestions(self, top_20_combinations: List[Dict], risk_level: str = "medium") -> List[Dict]:
        """購入方法提案"""
        # 期待値ベースの提案
        # リスクレベル別の提案
        # コスト最適化

    def save_predictions_to_json(self, predictions: Dict, output_path: str = None) -> str:
        """JSON保存"""
        # 予測結果のJSON形式保存
        # タイムスタンプ付きファイル名生成
```

### コマンドライン引数
```bash
# 完全統合実行
python -m kyotei_predictor.tools.prediction_tool --date 2024-07-12

# 特定会場のみ実行
python -m kyotei_predictor.tools.prediction_tool --date 2024-07-12 --venues KIRYU TAMAGAWA

# データ取得のみ実行
python -m kyotei_predictor.tools.prediction_tool --fetch-data --date 2024-07-12

# 予測のみ実行
python -m kyotei_predictor.tools.prediction_tool --prediction-only --date 2024-07-12
```

---

## 📈 性能・品質指標

### 予測性能
- **実行時間**: 会場別予測で数分以内
- **予測精度**: 192次元状態ベクトルで正確な予測実行
- **成功率**: テスト時100%（12/12レース）
- **メモリ使用量**: 適切な範囲内

### 出力品質
- **確率計算**: 正規化された確率値（合計1.0）
- **期待値計算**: 実際のオッズを使用した正確な期待値
- **購入提案**: リスクレベル別の最適化された提案
- **JSON形式**: 標準的なJSON形式で保存

### 運用性能
- **自動化率**: データ取得→予測→結果保存の90%以上
- **エラー処理**: 各段階での適切なエラーハンドリング
- **ログ出力**: 詳細な実行ログ・進捗表示

---

## 🎯 次のマイルストーン

### 短期目標（1-2週間）
1. **Web表示機能実装**
   - 静的HTMLファイルの作成（期限: 2025-07-20）
   - JavaScriptでのJSON読み込み・表示機能（期限: 2025-07-22）
   - 3連単上位20組の表示機能（期限: 2025-07-24）
   - 購入方法の提案表示機能（期限: 2025-07-25）
   - 基本的なソート・フィルタ機能（期限: 2025-07-26）

2. **深夜自動実行開始**
   - スケジューラ設定（期限: 2025-07-27）
   - エラー処理・アラート機能
   - 運用監視システム

### 中期目標（1-2ヶ月）
1. **完全自動化システム**
   - 深夜自動実行の安定化
   - エラー処理・アラート機能の強化
   - 運用監視システムの構築

2. **予測精度向上**
   - 継続的なモデル改善
   - 新規特徴量の追加
   - 予測精度の監視

3. **2024年4月以降のデータ取得**
   - 月次データ取得の継続
   - データ品質の維持

### 長期目標（3-6ヶ月）
1. **ビジネス展開準備**
   - リアルタイム予測システム
   - 自動モデル更新
   - 商用化準備

---

## 📚 関連ドキュメント

### 運用・ステータス
- [NEXT_STEPS.md](NEXT_STEPS.md) - 直近のTODO・優先度
- [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) - 現在状況サマリー
- [PREDICTION_TOOL_IMPLEMENTATION_TASKS.md](PREDICTION_TOOL_IMPLEMENTATION_TASKS.md) - 実装タスク詳細

### 設計・開発
- [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) - 開発ロードマップ
- [BATCH_SYSTEM_CURRENT_STATUS.md](BATCH_SYSTEM_CURRENT_STATUS.md) - バッチシステム状況

---

## 📝 更新履歴

- **2025-07-13**: 予想ツール実装完了、テスト成功確認、バージョン2.0に更新
- **2025-07-11**: 予想ツール仕様確定、購入方法提案機能追加、バージョン1.2に更新
- **2025-01-XX**: 初期設計・計画策定 