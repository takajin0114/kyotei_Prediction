"""
B案ベースラインモデルの学習・予測ランナー（infrastructure 層）。

既存の state vector（build_race_state_vector）を入力とし、
3連単120クラスのスコア（確率）を出力する。既存 betting / verify と互換の形式を返す。
TODO: 将来 LightGBM / XGBoost に差し替えやすいよう、モデル生成は create_baseline_model() に集約する。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from kyotei_predictor.pipelines.state_vector import TRIFECTA_ORDER

# 3連単 120 クラス（1-2-3 等の文字列とインデックスの対応）
TRIFECTA_STRINGS = [f"{a}-{b}-{c}" for a, b, c in TRIFECTA_ORDER]


def trifecta_to_class_index(combination: str) -> int:
    """3連単文字列 '1-2-3' をクラスインデックス 0..119 に変換する。"""
    parts = combination.strip().replace(" ", "").split("-")
    if len(parts) != 3:
        raise ValueError(f"invalid combination: {combination}")
    t = (int(parts[0]), int(parts[1]), int(parts[2]))
    for i, order in enumerate(TRIFECTA_ORDER):
        if order == t:
            return i
    raise ValueError(f"combination not in TRIFECTA_ORDER: {combination}")


def create_baseline_model(
    use_sklearn: bool = True,
    n_estimators: int = 50,
    max_depth: int = 10,
    random_state: int = 42,
) -> Any:
    """
    ベースライン用の分類器を生成する。

    現状は scikit-learn の RandomForestClassifier。
    TODO: use_sklearn=False で LightGBM / XGBoost を返すオプションを追加する。

    Returns:
        fit(X, y) と predict_proba(X) を持つオブジェクト
    """
    if use_sklearn:
        try:
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
            )
        except ImportError:
            from sklearn.linear_model import LogisticRegression
            return LogisticRegression(max_iter=500, random_state=random_state)
    # TODO: import lightgbm / xgboost and return LGBMClassifier or XGBClassifier
    raise NotImplementedError("use_sklearn=False は未実装（LightGBM/XGBoost 用）")


def predict_proba_120(model: Any, state: np.ndarray) -> np.ndarray:
    """
    1レース分の状態ベクトルから 120 クラスの確率を返す。

    Args:
        model: predict_proba を持つモデル
        state: shape=(state_dim,) の float 配列

    Returns:
        shape=(120,) の確率配列（合計1に正規化されていなくても可。verify ではスコアとして利用）
    """
    X = state.reshape(1, -1)
    proba = model.predict_proba(X)[0]
    if len(proba) != 120:
        # 多クラスで 120 出ない場合のフォールバック（通常は 120）
        pad = np.zeros(120, dtype=np.float32)
        pad[: min(len(proba), 120)] = proba[:120]
        if pad.sum() > 0:
            pad = pad / pad.sum()
        return pad
    return np.asarray(proba, dtype=np.float32)


def scores_to_all_combinations(proba: np.ndarray) -> List[Dict[str, Any]]:
    """
    120 クラスのスコアを、既存 prediction 形式の all_combinations に変換する。

    verify_predictions / betting_selector が期待する形式:
    [ {"combination": "1-2-3", "probability": float, "expected_value": 0, "rank": 1}, ... ]
    確率降順で rank 1..120 を付与。expected_value は B案最小では 0 固定。
    """
    order = np.argsort(-proba)
    out = []
    for rank, idx in enumerate(order, start=1):
        out.append({
            "combination": TRIFECTA_STRINGS[idx],
            "probability": float(proba[idx]),
            "expected_value": 0.0,
            "rank": rank,
        })
    return out
