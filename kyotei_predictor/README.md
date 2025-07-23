# 競艇予測システム (Kyotei Predictor)

> **注記**: 詳細な設計・運用ルールはdocs/配下に集約しています。全体像・詳細は[../README.md](../README.md)・[../docs/README.md](../docs/README.md)・各設計書を参照してください。

## 概要

競艇レースの3連単予測を行う強化学習システムです。PPO（Proximal Policy Optimization）アルゴリズムと段階的報酬設計を使用して、的中率の向上を実現しています。

## 主要ディレクトリ・参照先
- [../README.md](../README.md) - プロジェクト全体概要・索引
- [../docs/README.md](../docs/README.md) - ドキュメント全体ガイド
- [../docs/integration_design.md](../docs/integration_design.md) - システム統合設計
- [../docs/DEVELOPMENT_ROADMAP.md](../docs/DEVELOPMENT_ROADMAP.md) - 開発ロードマップ
- [data/README.md](data/README.md) - データ運用ルール
- [pipelines/README.md](pipelines/README.md) - パイプライン運用
- [tools/README.md](tools/README.md) - ツール群運用

---

# 以下、従来の内容（構造・成果等）は現状維持

## 現在の成果

### 段階的報酬設計の成功
- **的中率**: 0.83% → 6%（約7倍改善）
- **学習の安定性**: 大幅向上
- **データ品質**: 不完全なデータの適切なスキップ
- **実際の的中**: 330, 2560, 210の報酬を達成

### 技術的ブレークスルー
- 部分的中にも報酬を与える段階的報酬設計
- データ品質チェックによる信頼性向上
- 学習効率の大幅改善

## プロジェクト構造

```
kyotei_predictor/
├── app.py                          # Webアプリケーション
├── config/                         # 設定ファイル
│   ├── settings.py                 # 基本設定
│   └── optuna_config.json         # Optuna設定
├── data/                          # データディレクトリ
│   ├── raw/                       # 生データ
│   ├── processed/                 # 処理済みデータ
│   ├── results/                   # 結果データ
│   └── logs/                      # ログファイル
├── pipelines/                     # データ処理パイプライン
│   ├── data_preprocessor.py       # データ前処理
│   ├── feature_enhancer.py        # 特徴量エンジニアリング
│   ├── db_integration.py          # データベース統合
│   └── kyotei_env.py              # 競艇環境
├── tools/                         # ツール群
│   ├── batch/                     # バッチ処理
│   │   ├── train_graduated_reward.py      # 段階的報酬学習
│   │   └── train_extended_graduated_reward.py  # 拡張学習
│   ├── evaluation/                # 評価ツール
│   │   └── evaluate_graduated_reward_model.py  # 詳細評価
│   └── optimization/              # 最適化ツール
│       └── optimize_graduated_reward.py   # ハイパーパラメータ最適化
├── static/                        # 静的ファイル
│   ├── predictions.css            # Web表示機能のスタイルシート
│   ├── predictions.js             # Web表示機能のJavaScript
│   ├── test_server.py             # ローカルテスト用HTTPサーバー
│   └── stop_test_server.py        # テストサーバーの安全な停止スクリプト
├── templates/                     # HTMLテンプレート
└── utils/                         # ユーティリティ
```

## 開発ロードマップ

詳細な開発計画は [docs/DEVELOPMENT_ROADMAP.md](../docs/DEVELOPMENT_ROADMAP.md) を参照してください。

### Phase 1: 即座に実行可能な改善（1-2週間）
1. **詳細なモデル評価**
   ```bash
   python -m kyotei_predictor.tools.evaluation.evaluate_graduated_reward_model
   ```

2. **ハイパーパラメータ最適化**
   ```bash
   python -m kyotei_predictor.tools.optimization.optimize_graduated_reward
   ```

3. **特徴量エンジニアリングの改善**

### Phase 2: 中期的な改善（1-2ヶ月）
1. **より長期間の学習**
   ```bash
   python -m kyotei_predictor.tools.batch.train_extended_graduated_reward
   ```

2. **アンサンブル学習**
3. **リアルタイム予測システム**

### Phase 3: 長期的な発展（3-6ヶ月）
1. **高度な特徴量エンジニアリング**
2. **マルチタスク学習**
3. **説明可能AI（XAI）**

### Phase 4: 実用化と展開（6ヶ月以降）
1. **本格的な予測サービス**
2. **継続的な改善**
3. **ビジネス展開**

## セットアップ

### 1. 環境構築
```bash
# 仮想環境作成
python -m venv venv311
source venv311/bin/activate  # Linux/Mac
# または
venv311\Scripts\activate     # Windows

# 依存関係インストール
pip install -r requirements.txt
```

### 2. データ準備
```bash
# データディレクトリ作成
mkdir -p kyotei_predictor/data/raw
mkdir -p kyotei_predictor/data/processed
mkdir -p kyotei_predictor/data/results
```

### 3. 設定ファイル
`kyotei_predictor/config/settings.py` を環境に合わせて編集してください。

## 使用方法

### 基本的な学習
```bash
# 段階的報酬設計での学習
python -m kyotei_predictor.tools.batch.train_graduated_reward
```

### モデル評価
```bash
# 学習済みモデルの詳細評価
python -m kyotei_predictor.tools.evaluation.evaluate_graduated_reward_model
```

### ハイパーパラメータ最適化
```bash
# Optunaを使用した自動最適化
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward
```

### 拡張学習
```bash
# より長期間の学習（100万ステップ）
python -m kyotei_predictor.tools.batch.train_extended_graduated_reward
```

### Webアプリケーション
```bash
# 予測システムの起動
python kyotei_predictor/app.py
```

### Web表示機能のテスト
```bash
# テストサーバーの起動
python kyotei_predictor/static/test_server.py

# テストサーバーの安全な停止（推奨）
python kyotei_predictor/static/stop_test_server.py

# 自動テストの実行
python kyotei_predictor/tests/run_web_tests.py
```

**注意**: テストサーバー停止時は必ず`stop_test_server.py`を使用してください。
`taskkill /f /im python.exe`は他のバッチ処理も停止してしまうため使用禁止です。

## 主要な技術

### 強化学習
- **アルゴリズム**: PPO (Proximal Policy Optimization)
- **環境**: カスタム競艇環境
- **報酬設計**: 段階的報酬（部分的中にも報酬）

### データ処理
- **前処理**: 正規化、欠損値処理
- **特徴量エンジニアリング**: 選手成績、レース条件
- **データ品質チェック**: 不完全データのスキップ

### 最適化
- **ハイパーパラメータ最適化**: Optuna
- **モデル評価**: 的中率、報酬分布分析
- **可視化**: 学習曲線、的中率推移

## 期待される成果

### 短期的（1ヶ月以内）
- **的中率**: 6% → 10-15%
- **学習の安定性**: さらに向上
- **予測の信頼性**: 大幅改善

### 中期的（3ヶ月以内）
- **的中率**: 15% → 20-25%
- **実用的な予測システム**: 完成
- **アンサンブル学習**: 実装完了

### 長期的（6ヶ月以降）
- **的中率**: 25% → 30%以上
- **本格的なサービス**: 開始
- **収益化**: 実現

## トラブルシューティング

### よくある問題

1. **データ不足エラー**
   - データディレクトリに十分なレースデータがあることを確認
   - データ品質チェックを実行

2. **メモリ不足**
   - バッチサイズを小さくする
   - より少ないステップ数で学習

3. **学習が進まない**
   - 段階的報酬設計を使用
   - ハイパーパラメータの調整

## 貢献

プロジェクトへの貢献を歓迎します。以下の手順でお願いします：

1. このリポジトリをフォーク
2. 機能ブランチを作成
3. 変更をコミット
4. プルリクエストを作成

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 連絡先

質問や提案がある場合は、GitHubのIssuesページをご利用ください。

---

**注意**: このシステムは研究・学習目的で開発されています。実際の競艇予想には十分な検証が必要です。