# 競艇予測システム - ドキュメント

## 📋 目次

### 📊 プロジェクト概要
- [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) - 現在の状況サマリー
- [DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) - ドキュメント標準

### 🚀 今後の方針
- [future_strategy.md](future_strategy.md) - 今後の方針と戦略

### 🔧 開発者向けドキュメント
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - 開発者ガイド
- [API_SPECIFICATION.md](API_SPECIFICATION.md) - API仕様書

### 📁 運用ドキュメント
- [operations/](operations/) - 運用関連ドキュメント

### 📋 要件ドキュメント
- [requirements/](requirements/) - 要件関連ドキュメント

### 🌐 Web表示ドキュメント
- [web_display/](web_display/) - Web表示関連ドキュメント

---

## 🎯 プロジェクト概要

競艇予測システムは、強化学習を用いた競艇の3連単予測システムです。

### 主要機能
- **段階的報酬設計**: 的中率1.70%（理論値の約2倍）
- **最適化システム**: Optunaによる自動最適化
- **監視システム**: リアルタイム進捗監視
- **評価システム**: 客観的性能評価
- **統合ユーティリティ**: 標準化された設定管理・ログ機能・エラーハンドリング

### 技術スタック
- **強化学習**: Stable-Baselines3 (PPO)
- **最適化**: Optuna
- **データ処理**: pandas, numpy
- **可視化**: matplotlib
- **統合ユーティリティ**: カスタム設定管理・ログ機能・エラーハンドリング

### 現在の成果
- **的中率**: 1.70%（理論値0.83%の約2倍）
- **学習効率**: 16.2倍
- **報酬安定性**: 52.5%
- **総合スコア**: 40.5/100

---

## 🏗️ 新しいアーキテクチャ（v4.1）

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

### 設定管理構造
```
kyotei_predictor/config/
├── config.json          # デフォルト設定
└── README.md           # 設定ドキュメント
```

### テスト構造
```
kyotei_predictor/tests/
├── test_utils.py        # 統合ユーティリティテスト
└── README.md           # テストドキュメント
```

---

## 🔧 使用方法

### 1. **基本インポート**
```python
from kyotei_predictor.utils import (
    KyoteiUtils, Config, setup_logger, VenueMapper,
    KyoteiError, DataError, APIError
)
```

### 2. **設定管理**
```python
config = Config()
data_dir = config.get_data_dir()
timeout = config.get_api_timeout()
```

### 3. **ログ機能**
```python
logger = setup_logger("my_module", log_file="logs/app.log")
logger.info("処理開始")
```

### 4. **会場マッピング**
```python
venue_name = VenueMapper.get_venue_name(StadiumTelCode.KIRYU)
venue_code = VenueMapper.get_venue_code(StadiumTelCode.KIRYU)
```

### 5. **エラーハンドリング**
```python
@handle_exception
def my_function():
    # 処理
    pass
```

---

## 📈 今後の方針

詳細な今後の方針については、[future_strategy.md](future_strategy.md)をご参照ください。

### 主要な改善点
1. **段階的最適化アプローチ** - 月別最適化の継続
2. **報酬設計の改善** - 的中報酬の強化
3. **学習パラメータの強化** - 学習時間の延長
4. **アンサンブル学習の導入** - 予測精度の向上
5. **既存コードの移行** - 統合ユーティリティの活用

### 目標
- **短期的目標（1ヶ月）**: 的中率2.5%以上
- **中期的目標（3ヶ月）**: 的中率3.0%以上
- **長期的目標（6ヶ月）**: 的中率4.0%以上

---

## 🔧 開発環境

### 必要条件
- Python 3.8+
- 仮想環境（venv）
- 必要なパッケージ（requirements.txt）

### セットアップ
```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 実行方法
```bash
# 最適化の実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward

# 監視の実行
python monitor_optimization.py

# 評価の実行
python -m kyotei_predictor.tools.evaluation.evaluate_graduated_reward_model

# テストの実行
python -m pytest kyotei_predictor/tests/
```

---

## 📊 成果物

### 最適化結果
- **最適化データベース**: `optuna_studies/`
- **最適化結果**: `optuna_results/`
- **学習済みモデル**: `optuna_models/`

### 評価結果
- **評価結果**: `outputs/`
- **分析結果**: `analysis_*.py`

### ログ
- **学習ログ**: `optuna_logs/`
- **監視ログ**: `data/logs/`

### テスト結果
- **テスト結果**: `kyotei_predictor/tests/`
- **統合テスト**: 自動テスト実行

---

## 🤝 貢献

プロジェクトへの貢献については、[DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md)をご参照ください。

---

*最終更新: 2025年1月27日*  
*プロジェクト: 競艇予測システム*  
*バージョン: 4.1（リファクタリング完了）* 