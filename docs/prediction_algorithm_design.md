# 予測アルゴリズム設計書

**役割**: 競艇予測システムのアルゴリズム設計・運用ルール・拡張方針を記載
**参照先**: [../README.md](../README.md), [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)
**最終更新日**: 2025-07-09

---

## 概要
- 本ドキュメントは、3連単確率計算・段階的報酬設計・強化学習アルゴリズム（PPO）・特徴量設計・評価指標など、予測アルゴリズム全体の設計・運用ルールを記載します。

## 索引・関連ドキュメント
- [TRIFECTA_IMPROVEMENT_PLAN.md](TRIFECTA_IMPROVEMENT_PLAN.md) - 3連単確率計算改善
- [GRADUATED_REWARD_IMPLEMENTATION.md](GRADUATED_REWARD_IMPLEMENTATION.md) - 段階的報酬設計
- [LEARNING_DEBUGGING_PLAN.md](LEARNING_DEBUGGING_PLAN.md) - 学習デバッグ計画
- [LEARNING_DEBUGGING_RESULTS.md](LEARNING_DEBUGGING_RESULTS.md) - 学習デバッグ結果

---

## 現状のアルゴリズム設計・運用ルール
- 3連単確率計算はsoftmax正規化・機材重視重み付け・2着/3着重み調整
- 強化学習はPPO＋段階的報酬設計で安定学習を実現
- 特徴量設計・前処理・評価指標の標準化
- モデル評価・失敗パターン分析・再学習サイクルの自動化

## 成果・課題・今後のTODO
- 成果: 的中率7倍改善、安定学習・再現性向上
- 課題: 特徴量のさらなる拡充・モデル構造の最適化
- TODO: 新規特徴量追加・アンサンブル・XAI・API連携

## 更新履歴
- 2025-07-09: 現状設計・運用ルール・索引・成果・課題・TODOを追記

---

## モデルAPI・クラス・関数仕様（API_SPECIFICATION.mdより集約）

### TrifectaDependentModel
- ファイル: `kyotei_predictor/pipelines/trifecta_dependent_model.py`
- 着順依存性・艇間相関を考慮した3連単確率予測モデル

#### 主要メソッド
- `learn_conditional_probabilities(data_dir: str, max_files: int = 1000) -> None`
  - 条件付き確率・艇間相関を学習
- `calculate_dependent_probabilities(race_data: Dict[str, Any]) -> Dict[str, Any]`
  - 着順依存型3連単確率を計算
- `save_model(file_path: str) -> bool`
  - 学習済みモデルを保存
- `load_model(file_path: str) -> bool`
  - 学習済みモデルを読み込み

### 共通ユーティリティAPI（KyoteiUtils）
- ファイル: `kyotei_predictor/utils/common.py`
- 主要メソッド:
  - `load_json_file(file_path: str) -> Dict[str, Any]`
  - `save_json_file(data: Dict[str, Any], file_path: str) -> bool`
  - `extract_race_result(race_data: Dict[str, Any]) -> Optional[Tuple[int, int, int]]`
  - `calculate_expected_value(probability: float, odds: float) -> float`
  - `is_profitable(expected_value: float, threshold: float = 1.0) -> bool`
  - `normalize_probabilities(probabilities: List[float]) -> List[float]`
  - `softmax(x: List[float], temperature: float = 1.0) -> List[float]`
  - `get_ranking_distribution(predictions: List[Dict[str, Any]], actual_result: Tuple[int, int, int]) -> Dict[str, Any]`
  - `calculate_hit_rates(results: List[Dict[str, Any]]) -> Dict[str, float]`
  - `validate_race_data(race_data: Dict[str, Any]) -> bool`