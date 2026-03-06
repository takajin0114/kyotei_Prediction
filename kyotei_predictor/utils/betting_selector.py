#!/usr/bin/env python3
"""
買い目選定モジュール（共通基盤）

予測候補（候補とスコア）を受け取り、購入する組み合わせを返す。
B案移行後も同じインターフェースで EV 戦略等に拡張しやすい設計とする。
"""

from typing import Dict, List, Any, Optional

# 戦略名（config の betting.strategy と一致）
STRATEGY_SINGLE = "single"
STRATEGY_TOP_N = "top_n"
STRATEGY_THRESHOLD = "threshold"
STRATEGY_EV = "ev"  # TODO: 将来 EV ベースの本実装に拡張


def _get_combination(c: Dict[str, Any]) -> str:
    """候補辞書から combination 文字列を取得（'1-2-3' 形式）"""
    return (c.get("combination") or "").strip()


def _get_score(c: Dict[str, Any]) -> float:
    """候補辞書からスコア（確率）を取得。キーは probability または score。"""
    return float(c.get("probability", c.get("score", 0.0)))


def select_single(predictions: List[Dict[str, Any]]) -> List[str]:
    """
    1位予想のみ購入（常に1点買い）。

    Args:
        predictions: 予測候補リスト（combination, probability 等）。確率降順を想定。

    Returns:
        購入する combination のリスト（1要素）
    """
    if not predictions:
        return []
    comb = _get_combination(predictions[0])
    return [comb] if comb else []


def select_top_n(predictions: List[Dict[str, Any]], n: int) -> List[str]:
    """
    上位 N 点を購入。

    Args:
        predictions: 予測候補リスト。確率降順を想定。
        n: 購入する点数（1以上）。

    Returns:
        購入する combination のリスト
    """
    if n <= 0 or not predictions:
        return []
    out: List[str] = []
    for c in predictions[:n]:
        comb = _get_combination(c)
        if comb:
            out.append(comb)
    return out


def select_score_threshold(predictions: List[Dict[str, Any]], threshold: float) -> List[str]:
    """
    スコア（確率）が閾値以上の候補のみ購入。

    Args:
        predictions: 予測候補リスト。
        threshold: 閾値（この値以上を購入）。

    Returns:
        購入する combination のリスト
    """
    out: List[str] = []
    for c in predictions:
        if _get_score(c) >= threshold:
            comb = _get_combination(c)
            if comb:
                out.append(comb)
    return out


def select_ev(
    predictions: List[Dict[str, Any]],
    ev_threshold: float = 0.0,
    top_n_fallback: int = 5,
) -> List[str]:
    """
    EV（期待値）ベースの選定。将来拡張用。
    現時点では expected_value が閾値以上なら購入、該当がなければ上位 top_n_fallback でフォールバック。

    Args:
        predictions: 予測候補リスト（expected_value があれば使用）。
        ev_threshold: EV 閾値。
        top_n_fallback: 該当なし時のフォールバック点数。

    Returns:
        購入する combination のリスト
    """
    out: List[str] = []
    for c in predictions:
        ev = c.get("expected_value")
        if ev is not None:
            try:
                if float(ev) >= ev_threshold:
                    comb = _get_combination(c)
                    if comb:
                        out.append(comb)
            except (TypeError, ValueError):
                pass
    if not out:
        return select_top_n(predictions, top_n_fallback)
    return out


def select_bets(
    predictions: List[Dict[str, Any]],
    strategy: str = STRATEGY_SINGLE,
    top_n: int = 3,
    score_threshold: float = 0.05,
    ev_threshold: float = 0.0,
    **kwargs: Any,
) -> List[str]:
    """
    設定に応じて買い目を選定する共通入口。

    Args:
        predictions: 予測候補リスト（combination, probability 等）。
        strategy: "single" | "top_n" | "threshold" | "ev"
        top_n: strategy=top_n のときの N。
        score_threshold: strategy=threshold のときの閾値。
        ev_threshold: strategy=ev のときの EV 閾値。
        **kwargs: その他（将来拡張用）。

    Returns:
        購入する combination のリスト
    """
    strategy = (strategy or STRATEGY_SINGLE).strip().lower()
    if strategy == STRATEGY_SINGLE:
        return select_single(predictions)
    if strategy == STRATEGY_TOP_N:
        return select_top_n(predictions, top_n)
    if strategy == STRATEGY_THRESHOLD:
        return select_score_threshold(predictions, score_threshold)
    if strategy == STRATEGY_EV:
        return select_ev(predictions, ev_threshold=ev_threshold, top_n_fallback=top_n)
    return select_single(predictions)
