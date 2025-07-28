# 競艇予測システム - ドキュメント

## 📋 目次

### 📊 プロジェクト概要
- [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) - 現在の状況サマリー
- [DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) - ドキュメント標準

### 🚀 今後の方針
- [future_strategy.md](future_strategy.md) - 今後の方針と戦略

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

### 技術スタック
- **強化学習**: Stable-Baselines3 (PPO)
- **最適化**: Optuna
- **データ処理**: pandas, numpy
- **可視化**: matplotlib

### 現在の成果
- **的中率**: 1.70%（理論値0.83%の約2倍）
- **学習効率**: 16.2倍
- **報酬安定性**: 52.5%
- **総合スコア**: 40.5/100

---

## 📈 今後の方針

詳細な今後の方針については、[future_strategy.md](future_strategy.md)をご参照ください。

### 主要な改善点
1. **段階的最適化アプローチ** - 月別最適化の継続
2. **報酬設計の改善** - 的中報酬の強化
3. **学習パラメータの強化** - 学習時間の延長
4. **アンサンブル学習の導入** - 予測精度の向上

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

---

## 🤝 貢献

プロジェクトへの貢献については、[DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md)をご参照ください。

---

*最終更新: 2025年7月27日*
*プロジェクト: 競艇予測システム* 