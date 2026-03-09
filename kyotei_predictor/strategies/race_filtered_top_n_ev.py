"""
race_filtered_top_n_ev: レース単位のフィルタを通過したレースのみ top_n_ev で買い目選定。

3段構造: race_feature_calculation → race_filter → bet_selection
後から ranker に拡張しやすい設計。
"""

import math
from typing import Any, Dict, List, Optional

# 期待リターン = 確率 × オッズ（閾値 1.05 = 5% プラス）
def _expected_roi(probability: float, odds_ratio: float) -> float:
    return probability * odds_ratio


def _get_score(c: Dict[str, Any]) -> float:
    return float(c.get("probability", c.get("score", 0.0)))


def _get_odds_ratio(c: Dict[str, Any]) -> Optional[float]:
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


def _race_entropy(probs: List[float]) -> float:
    if not probs:
        return 0.0
    total = sum(probs)
    if total <= 0:
        return 0.0
    h = 0.0
    for p in probs:
        if p > 0:
            q = p / total
            h -= q * math.log(q + 1e-12)
    return h


def race_feature_calculation(
    combinations: List[Dict[str, Any]],
    ev_threshold_for_count: float = 1.15,
) -> Dict[str, float]:
    """
    各レースで race-level 指標を計算する。

    Returns:
        race_max_ev, race_mean_top3_ev, race_top1_prob, race_prob_gap_top1_top2,
        race_entropy, candidate_count_above_threshold
    """
    if not combinations:
        return {
            "race_max_ev": 0.0,
            "race_mean_top3_ev": 0.0,
            "race_top1_prob": 0.0,
            "race_prob_gap_top1_top2": 0.0,
            "race_entropy": 0.0,
            "candidate_count_above_threshold": 0,
        }
    probs = [_get_score(c) for c in combinations]
    evs: List[float] = []
    for c in combinations:
        ratio = _get_odds_ratio(c)
        if ratio is not None and ratio > 0:
            evs.append(_expected_roi(_get_score(c), ratio))
        else:
            evs.append(0.0)
    race_max_ev = max(evs) if evs else 0.0
    # 確率降順で top3 の EV の平均
    indexed = list(zip(probs, evs))
    indexed.sort(key=lambda x: -x[0])
    top3_evs = [e for _, e in indexed[:3] if e > 0]
    race_mean_top3_ev = sum(top3_evs) / len(top3_evs) if top3_evs else 0.0
    race_top1_prob = indexed[0][0] if indexed else 0.0
    race_prob_gap_top1_top2 = (
        (indexed[0][0] - indexed[1][0]) if len(indexed) >= 2 else 0.0
    )
    race_ent = _race_entropy(probs)
    candidate_count_above_threshold = sum(1 for e in evs if e >= ev_threshold_for_count)
    return {
        "race_max_ev": race_max_ev,
        "race_mean_top3_ev": race_mean_top3_ev,
        "race_top1_prob": race_top1_prob,
        "race_prob_gap_top1_top2": race_prob_gap_top1_top2,
        "race_entropy": race_ent,
        "candidate_count_above_threshold": candidate_count_above_threshold,
    }


def race_filter(
    features: Dict[str, float],
    *,
    ev_min: float = 1.15,
    prob_gap_min: float = 0.05,
    entropy_max: float = 1.7,
    candidate_min: int = 1,
) -> bool:
    """
    race filter を適用。条件を満たすレースのみ True。
    """
    if features.get("race_max_ev", 0) < ev_min:
        return False
    if features.get("race_prob_gap_top1_top2", 0) < prob_gap_min:
        return False
    if features.get("race_entropy", float("inf")) > entropy_max:
        return False
    if features.get("candidate_count_above_threshold", 0) < candidate_min:
        return False
    return True


def bet_selection(
    combinations: List[Dict[str, Any]],
    top_n: int,
    ev_threshold: float,
) -> List[str]:
    """
    filter 通過レースに対して top_n_ev を適用。betting_selector の select_top_n_ev に委譲。
    """
    from kyotei_predictor.utils.betting_selector import select_top_n_ev
    return select_top_n_ev(combinations, top_n, ev_threshold)


def select_race_filtered_top_n_ev(
    predictions: List[Dict[str, Any]],
    top_n: int,
    ev_threshold: float,
    *,
    ev_min: float = 1.15,
    prob_gap_min: float = 0.05,
    entropy_max: float = 1.7,
    candidate_min: int = 1,
    ev_threshold_for_count: float = 1.15,
) -> List[str]:
    """
    1) race_feature_calculation 2) race_filter 3) bet_selection の順で実行。
    filter を通過したレースのみ top_n_ev で買い目を返す。
    """
    features = race_feature_calculation(predictions, ev_threshold_for_count=ev_threshold_for_count)
    if not race_filter(
        features,
        ev_min=ev_min,
        prob_gap_min=prob_gap_min,
        entropy_max=entropy_max,
        candidate_min=candidate_min,
    ):
        return []
    return bet_selection(predictions, top_n, ev_threshold)
