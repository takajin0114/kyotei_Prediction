#!/usr/bin/env python3
"""
買い目選定モジュール（共通基盤）

予測候補（候補とスコア）を受け取り、購入する組み合わせを返す。
B案移行後も同じインターフェースで EV 戦略等に拡張しやすい設計とする。
"""

from typing import Dict, List, Any, Optional, Tuple, Union

# 戦略名（config の betting.strategy と一致）
STRATEGY_SINGLE = "single"
STRATEGY_TOP_N = "top_n"
STRATEGY_THRESHOLD = "threshold"
STRATEGY_EV = "ev"
STRATEGY_TOP_N_EV = "top_n_ev"  # 上位 top_n 候補のうち expected_roi >= ev_threshold のみ購入
STRATEGY_EV_THRESHOLD_ONLY = "ev_threshold_only"  # EV >= ev_threshold の全候補を購入（top_n 制限なし）

# EV 戦略のフォールバック: オッズなし or 閾値以上なし時に採用する上位点数
DEFAULT_EV_TOP_N_FALLBACK = 5


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


def _get_odds_ratio(c: Dict[str, Any]) -> Optional[float]:
    """候補辞書からオッズ（倍率）を取得。ratio または odds キー。"""
    r = c.get("ratio")
    if r is not None:
        try:
            return float(r)
        except (TypeError, ValueError):
            pass
    o = c.get("odds")
    if o is not None:
        try:
            return float(o)
        except (TypeError, ValueError):
            pass
    return None


def _compute_ev(probability: float, odds_ratio: float) -> float:
    """
    期待値（ネット）を計算。EV = 確率 × オッズ - 1。
    1 円賭けて odds_ratio 円返る場合の期待利得。
    """
    return probability * odds_ratio - 1.0


def _expected_roi(probability: float, odds_ratio: float) -> float:
    """期待リターン（expected_roi = probability × odds）。閾値 1.05 は 5% プラス。"""
    return probability * odds_ratio


def select_ev_threshold_only(
    predictions: List[Dict[str, Any]],
    ev_threshold: float,
) -> List[str]:
    """
    expected_roi >= ev_threshold の全候補を購入。top_n 制限なし。

    Args:
        predictions: 予測候補リスト（probability と ratio または odds が必要）
        ev_threshold: 期待リターン閾値（例: 1.05 = 5% プラス）

    Returns:
        購入する combination のリスト
    """
    if not predictions:
        return []
    out: List[str] = []
    for c in predictions:
        prob = _get_score(c)
        ratio = _get_odds_ratio(c)
        if ratio is not None and ratio > 0:
            roi = _expected_roi(prob, ratio)
            if roi >= ev_threshold:
                comb = _get_combination(c)
                if comb:
                    out.append(comb)
    return out


def select_top_n_ev(
    predictions: List[Dict[str, Any]],
    top_n: int,
    ev_threshold: float,
) -> List[str]:
    """
    上位 top_n 候補のうち、expected_roi >= ev_threshold の組み合わせのみ購入。
    オッズがない候補は EV 計算できないため対象外。

    Args:
        predictions: 予測候補リスト（probability と ratio または odds が必要）。
        top_n: 候補として見る上位点数。
        ev_threshold: 期待リターン閾値（例: 1.05 = 5% プラス）。

    Returns:
        購入する combination のリスト
    """
    if top_n <= 0 or not predictions:
        return []
    candidates = predictions[:top_n]
    out: List[str] = []
    for c in candidates:
        prob = _get_score(c)
        ratio = _get_odds_ratio(c)
        if ratio is not None and ratio > 0:
            roi = _expected_roi(prob, ratio)
            if roi >= ev_threshold:
                comb = _get_combination(c)
                if comb:
                    out.append(comb)
    return out


# EV メタデータのキー（execution_summary / ログ用）
EV_META_THRESHOLD = "ev_threshold"
EV_META_ADOPTED_COUNT = "ev_adopted_count"
EV_META_SELECTED_COUNT = "ev_selected_count"  # ev_adopted_count の別名（比較・ログ用）
EV_META_FALLBACK_USED = "fallback_used"
EV_META_FALLBACK_COUNT = "fallback_count"
EV_META_PURCHASED_COUNT = "purchased_count"
EV_META_FINAL_SELECTED_COUNT = "final_selected_count"  # purchased_count の別名（比較・ログ用）


def select_ev(
    predictions: List[Dict[str, Any]],
    ev_threshold: float = 0.0,
    top_n_fallback: int = DEFAULT_EV_TOP_N_FALLBACK,
    return_metadata: bool = False,
) -> Union[List[str], Tuple[List[str], Dict[str, Any]]]:
    """
    EV（期待値）ベースの選定。オッズがある候補について EV = 確率×オッズ-1 を計算し、
    閾値以上のみ購入。オッズがない・該当なしの場合は上位 top_n_fallback でフォールバック。

    Args:
        predictions: 予測候補リスト（probability と ratio または odds があれば EV 計算）。
        ev_threshold: EV 閾値（この値以上の組み合わせを購入）。
        top_n_fallback: オッズなし or 該当なし時のフォールバック点数。
        return_metadata: True のとき (list, metadata_dict) を返す。B案・比較用ログ用。

    Returns:
        return_metadata=False: 購入する combination のリスト
        return_metadata=True: (リスト, メタデータ辞書)。メタデータは ev_threshold, ev_adopted_count,
            fallback_used, fallback_count, purchased_count を含む。
    """
    if top_n_fallback <= 0:
        top_n_fallback = DEFAULT_EV_TOP_N_FALLBACK
    out: List[str] = []
    ev_adopted_count = 0
    for c in predictions:
        prob = _get_score(c)
        ratio = _get_odds_ratio(c)
        if ratio is not None and ratio > 0:
            ev = _compute_ev(prob, ratio)
            if ev >= ev_threshold:
                comb = _get_combination(c)
                if comb:
                    out.append(comb)
                    ev_adopted_count += 1
        else:
            ev = c.get("expected_value")
            if ev is not None:
                try:
                    if float(ev) >= ev_threshold:
                        comb = _get_combination(c)
                        if comb:
                            out.append(comb)
                            ev_adopted_count += 1
                except (TypeError, ValueError):
                    pass
    fallback_used = len(out) == 0
    if fallback_used:
        out = select_top_n(predictions, top_n_fallback)
    fallback_count = len(out) if fallback_used else 0
    purchased_count = len(out)

    if return_metadata:
        metadata = {
            EV_META_THRESHOLD: ev_threshold,
            EV_META_ADOPTED_COUNT: ev_adopted_count,
            EV_META_SELECTED_COUNT: ev_adopted_count,
            EV_META_FALLBACK_USED: fallback_used,
            EV_META_FALLBACK_COUNT: fallback_count,
            EV_META_PURCHASED_COUNT: purchased_count,
            EV_META_FINAL_SELECTED_COUNT: purchased_count,
        }
        return (out, metadata)
    return out


def select_bets(
    predictions: List[Dict[str, Any]],
    strategy: str = STRATEGY_SINGLE,
    top_n: int = 3,
    score_threshold: float = 0.05,
    ev_threshold: float = 0.0,
    return_metadata: bool = False,
    **kwargs: Any,
) -> Union[List[str], Tuple[List[str], Dict[str, Any]]]:
    """
    設定に応じて買い目を選定する共通入口。

    Args:
        predictions: 予測候補リスト（combination, probability 等）。
        strategy: "single" | "top_n" | "threshold" | "ev"
        top_n: strategy=top_n のときの N。
        score_threshold: strategy=threshold のときの閾値。
        ev_threshold: strategy=ev のときの EV 閾値。
        return_metadata: strategy=ev のとき True にすると (list, ev_metadata) を返す。比較・B案用。
        **kwargs: その他（将来拡張用）。

    Returns:
        return_metadata=False または strategy!=ev: 購入する combination のリスト
        return_metadata=True かつ strategy=ev: (リスト, EVメタデータ辞書)
    """
    strategy = (strategy or STRATEGY_SINGLE).strip().lower()
    if strategy == STRATEGY_SINGLE:
        return select_single(predictions)
    if strategy == STRATEGY_TOP_N:
        return select_top_n(predictions, top_n)
    if strategy == STRATEGY_THRESHOLD:
        return select_score_threshold(predictions, score_threshold)
    if strategy == STRATEGY_TOP_N_EV:
        return select_top_n_ev(predictions, top_n, ev_threshold)
    if strategy == STRATEGY_EV_THRESHOLD_ONLY:
        return select_ev_threshold_only(predictions, ev_threshold)
    if strategy == STRATEGY_EV:
        result = select_ev(
            predictions,
            ev_threshold=ev_threshold,
            top_n_fallback=top_n,
            return_metadata=return_metadata,
        )
        return result
    return select_single(predictions)
