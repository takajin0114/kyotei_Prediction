#!/usr/bin/env python3
"""
買い目選定モジュール（共通基盤）

予測候補（候補とスコア）を受け取り、購入する組み合わせを返す。
B案移行後も同じインターフェースで EV 戦略等に拡張しやすい設計とする。
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union

# 戦略名（config の betting.strategy と一致）
STRATEGY_SINGLE = "single"
STRATEGY_TOP_N = "top_n"
STRATEGY_THRESHOLD = "threshold"
STRATEGY_EV = "ev"
STRATEGY_TOP_N_EV = "top_n_ev"  # 上位 top_n 候補のうち expected_roi >= ev_threshold のみ購入
STRATEGY_TOP_N_EV_CONFIDENCE = "top_n_ev_confidence"  # EV×信頼度でスコア化し top_n 選抜
STRATEGY_RACE_FILTERED_TOP_N_EV = "race_filtered_top_n_ev"  # レースフィルタ通過後の top_n_ev
STRATEGY_TOP_N_EV_PROB_POOL = "top_n_ev_prob_pool"  # 確率上位 pool_k に候補を限定し、その中で top_n_ev（または EV×confidence）で選抜
STRATEGY_TOP_N_EV_POWER_PROB = "top_n_ev_power_prob"  # EV_adj = (pred_prob ** alpha) * odds でスコア化し、ev_threshold 以上から top_n 選抜
STRATEGY_TOP_N_EV_GAP_FILTER = "top_n_ev_gap_filter"  # ev_gap = ev_rank1 - ev_rank2。ev_gap < threshold ならレースを skip
STRATEGY_TOP_N_EV_GAP_FILTER_ENTROPY = "top_n_ev_gap_filter_entropy"  # ev_gap filter + skip if race_entropy > entropy_threshold
STRATEGY_TOP_N_EV_GAP_FILTER_ODDS_BAND = "top_n_ev_gap_filter_odds_band"  # ev_gap filter + skip if odds_rank1 < odds_low or > odds_high
STRATEGY_TOP_N_EV_GAP_FILTER_ODDS_BAND_BET_LIMIT = "top_n_ev_gap_filter_odds_band_bet_limit"  # 上記 + 1レースあたり最大 max_bets_per_race 点に制限
STRATEGY_TOP_N_EV_GAP_VENUE_FILTER = "top_n_ev_gap_venue_filter"  # ev_gap filter + 会場別 ev_threshold（venue_ev_config で指定）
STRATEGY_TOP_N_EV_CONDITIONAL_PROB_GAP = "top_n_ev_conditional_prob_gap"  # pred_prob_gap 帯ごとに (top_n, ev) を切り替え
STRATEGY_EV_THRESHOLD_ONLY = "ev_threshold_only"  # EV >= ev_threshold の全候補を購入（top_n 制限なし）

# top_n_ev_confidence の confidence_type
CONFIDENCE_PRED_PROB = "pred_prob"
CONFIDENCE_PROB_GAP = "prob_gap"
CONFIDENCE_ENTROPY_ADJUSTED = "entropy_adjusted"

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


def _race_entropy(probs: List[float]) -> float:
    """
    同一レース内の確率分布のエントロピー。
    H = -sum(p * log(p)) for p in probs where p > 0.
    """
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


def _prob_gap_top1_top2(probs: List[float]) -> float:
    """
    同一レース内の 1 位と 2 位の確率差。
    降順で top1 - top2。要素が 1 つ以下なら 0。
    """
    if len(probs) < 2:
        return 0.0
    sorted_probs = sorted(probs, reverse=True)
    return sorted_probs[0] - sorted_probs[1]


def select_top_n_ev_confidence(
    predictions: List[Dict[str, Any]],
    top_n: int,
    ev_threshold: float,
    confidence_type: str = CONFIDENCE_PRED_PROB,
) -> List[str]:
    """
    EV >= ev_threshold の候補のうち、selection_score = ev × confidence の高い順に top_n 件選ぶ。
    confidence は confidence_type に応じて pred_prob / prob_gap / entropy_adjusted のいずれか。

    Args:
        predictions: 予測候補リスト（同一レースの all_combinations を想定）。probability と ratio 必須。
        top_n: 選ぶ件数。
        ev_threshold: 期待リターン閾値（expected_roi >= ev_threshold のみ対象）。
        confidence_type: "pred_prob" | "prob_gap" | "entropy_adjusted"

    Returns:
        購入する combination のリスト
    """
    if top_n <= 0 or not predictions:
        return []
    probs = [_get_score(c) for c in predictions]
    ratio_ok = [_get_odds_ratio(c) for c in predictions]
    ev_list = []
    for i, c in enumerate(predictions):
        prob = probs[i]
        ratio = ratio_ok[i]
        if ratio is None or ratio <= 0:
            continue
        ev = _expected_roi(prob, ratio)
        if ev < ev_threshold:
            continue
        ev_list.append((i, ev, prob))
    if not ev_list:
        return []

    race_ent = _race_entropy(probs)
    prob_gap = _prob_gap_top1_top2(probs)
    entropy_adj = 1.0 / (1.0 + race_ent) if race_ent is not None else 1.0

    scored = []
    for idx, ev, prob in ev_list:
        c = predictions[idx]
        if confidence_type == CONFIDENCE_PRED_PROB:
            conf = prob
        elif confidence_type == CONFIDENCE_PROB_GAP:
            conf = max(prob_gap, 1e-6)
        elif confidence_type == CONFIDENCE_ENTROPY_ADJUSTED:
            conf = entropy_adj
        else:
            conf = prob
        selection_score = ev * conf
        comb = _get_combination(c)
        if comb:
            scored.append((selection_score, comb))
    scored.sort(key=lambda x: -x[0])
    return [comb for _, comb in scored[:top_n]]


def select_top_n_ev_prob_pool(
    predictions: List[Dict[str, Any]],
    pool_k: int,
    top_n: int,
    ev_threshold: float,
    confidence_type: Optional[str] = None,
) -> List[str]:
    """
    確率上位 pool_k 件に候補を限定し、その中で EV >= ev_threshold の候補から top_n を選ぶ。
    confidence_type を指定した場合は、限定候補内で EV×confidence の高い順に top_n 選抜。

    Args:
        predictions: 予測候補リスト（確率降順を想定）。probability と ratio 必須。
        pool_k: 候補プールのサイズ（pred_prob 上位 K 件）。
        top_n: 選抜する点数。
        ev_threshold: 期待リターン閾値。
        confidence_type: None のときは top_n_ev。 "pred_prob" | "prob_gap" のときは EV×confidence で top_n 選抜。

    Returns:
        購入する combination のリスト
    """
    if pool_k <= 0 or top_n <= 0 or not predictions:
        return []
    pool = predictions[:pool_k]
    if confidence_type and confidence_type.strip().lower() in (CONFIDENCE_PROB_GAP, "prob_gap"):
        return select_top_n_ev_confidence(
            pool, top_n, ev_threshold, confidence_type=CONFIDENCE_PROB_GAP
        )
    if confidence_type and confidence_type.strip().lower() in (CONFIDENCE_PRED_PROB, "pred_prob"):
        return select_top_n_ev_confidence(
            pool, top_n, ev_threshold, confidence_type=CONFIDENCE_PRED_PROB
        )
    return select_top_n_ev(pool, top_n, ev_threshold)


def select_top_n_ev_conditional_prob_gap(
    predictions: List[Dict[str, Any]],
    band_edges: List[float],
    band_params: List[Tuple[int, float]],
) -> List[str]:
    """
    pred_prob_gap（1位と2位の確率差）の帯ごとに (top_n, ev_threshold) を切り替えて top_n_ev を適用する。
    band_edges: 閾値のリスト（昇順）。例 [0.03, 0.07] → 帯は [0, 0.03), [0.03, 0.07), [0.07, 1.0]。
    band_params: 各帯に対する (top_n, ev_threshold) のリスト。len(band_params) == len(band_edges) + 1。

    Args:
        predictions: 予測候補リスト（同一レースの all_combinations）。probability と ratio 必須。
        band_edges: 確率差の境界（昇順）。
        band_params: 帯ごとの (top_n, ev_threshold)。

    Returns:
        購入する combination のリスト
    """
    if not predictions or not band_edges or not band_params:
        return []
    if len(band_params) != len(band_edges) + 1:
        return []
    probs = [_get_score(c) for c in predictions]
    prob_gap = _prob_gap_top1_top2(probs)
    band_idx = 0
    for i, edge in enumerate(band_edges):
        if prob_gap < edge:
            band_idx = i
            break
    else:
        band_idx = len(band_edges)
    top_n, ev_threshold = band_params[band_idx]
    return select_top_n_ev(predictions, top_n, ev_threshold)


def select_top_n_ev_gap_filter(
    predictions: List[Dict[str, Any]],
    top_n: int,
    ev_threshold: float,
    ev_gap_threshold: float,
) -> List[str]:
    """
    ev_gap = ev_rank1 - ev_rank2（EV は expected_roi = prob * odds）。
    ev_gap < ev_gap_threshold ならそのレースを skip（購入なし）。
    そうでなければ top_n_ev と同様に選抜する。

    Args:
        predictions: 予測候補リスト（同一レースの all_combinations）。probability と ratio 必須。
        top_n: 選抜する点数。
        ev_threshold: 期待リターン閾値。
        ev_gap_threshold: 1位と2位の EV 差の閾値。これ未満ならレースを skip。

    Returns:
        購入する combination のリスト（skip 時は []）
    """
    if top_n <= 0 or not predictions:
        return []
    ev_list: List[Tuple[float, int]] = []
    for i, c in enumerate(predictions):
        prob = _get_score(c)
        ratio = _get_odds_ratio(c)
        if ratio is None or ratio <= 0:
            continue
        ev = _expected_roi(prob, ratio)
        ev_list.append((ev, i))
    if not ev_list:
        return []
    ev_list.sort(key=lambda x: -x[0])
    ev_rank1 = ev_list[0][0]
    ev_rank2 = ev_list[1][0] if len(ev_list) >= 2 else 0.0
    ev_gap = ev_rank1 - ev_rank2
    if ev_gap < ev_gap_threshold:
        return []
    return select_top_n_ev(predictions, top_n, ev_threshold)


def select_top_n_ev_gap_filter_entropy(
    predictions: List[Dict[str, Any]],
    top_n: int,
    ev_threshold: float,
    ev_gap_threshold: float,
    entropy_threshold: float,
) -> List[str]:
    """
    top_n_ev_gap_filter に entropy フィルタを追加。
    race_entropy > entropy_threshold ならレースを skip。
    それ以外は select_top_n_ev_gap_filter と同様。

    Args:
        predictions: 予測候補リスト（同一レースの all_combinations）。
        top_n: 選抜する点数。
        ev_threshold: 期待リターン閾値。
        ev_gap_threshold: 1位と2位の EV 差の閾値。これ未満ならレースを skip。
        entropy_threshold: レースエントロピーがこれを超えたらレースを skip。

    Returns:
        購入する combination のリスト（skip 時は []）
    """
    if top_n <= 0 or not predictions:
        return []
    probs = [_get_score(c) for c in predictions]
    race_ent = _race_entropy(probs)
    if race_ent > entropy_threshold:
        return []
    return select_top_n_ev_gap_filter(
        predictions, top_n, ev_threshold, ev_gap_threshold=ev_gap_threshold
    )


def select_top_n_ev_gap_filter_odds_band(
    predictions: List[Dict[str, Any]],
    top_n: int,
    ev_threshold: float,
    ev_gap_threshold: float,
    odds_low: float,
    odds_high: float,
) -> List[str]:
    """
    top_n_ev_gap_filter にオッズ帯フィルタを追加。
    odds_rank1（EV 1位の組み合わせのオッズ）が odds_low 未満または odds_high を超えるならレースを skip。
    それ以外は select_top_n_ev_gap_filter と同様。

    Args:
        predictions: 予測候補リスト（同一レースの all_combinations）。probability と ratio 必須。
        top_n: 選抜する点数。
        ev_threshold: 期待リターン閾値。
        ev_gap_threshold: 1位と2位の EV 差の閾値。これ未満ならレースを skip。
        odds_low: 1位オッズがこれ未満ならレースを skip。
        odds_high: 1位オッズがこれを超えたらレースを skip。

    Returns:
        購入する combination のリスト（skip 時は []）
    """
    if top_n <= 0 or not predictions:
        return []
    ev_list: List[Tuple[float, int]] = []
    for i, c in enumerate(predictions):
        prob = _get_score(c)
        ratio = _get_odds_ratio(c)
        if ratio is None or ratio <= 0:
            continue
        ev = _expected_roi(prob, ratio)
        ev_list.append((ev, i))
    if not ev_list:
        return []
    ev_list.sort(key=lambda x: -x[0])
    rank1_idx = ev_list[0][1]
    odds_rank1 = _get_odds_ratio(predictions[rank1_idx])
    if odds_rank1 is None or odds_rank1 < odds_low or odds_rank1 > odds_high:
        return []
    return select_top_n_ev_gap_filter(
        predictions, top_n, ev_threshold, ev_gap_threshold=ev_gap_threshold
    )


def select_top_n_ev_gap_filter_odds_band_bet_limit(
    predictions: List[Dict[str, Any]],
    top_n: int,
    ev_threshold: float,
    ev_gap_threshold: float,
    odds_low: float,
    odds_high: float,
    max_bets_per_race: int,
) -> List[str]:
    """
    top_n_ev_gap_filter_odds_band の結果を 1 レースあたり最大 max_bets_per_race 点に制限する。
    EV 順で選ばれた組み合わせの先頭 max_bets_per_race 件のみ返す。

    Args:
        predictions: 予測候補リスト（同一レースの all_combinations）。
        top_n: 選抜する点数（odds_band 内部で使用）。
        ev_threshold: 期待リターン閾値。
        ev_gap_threshold: 1位と2位の EV 差の閾値。
        odds_low: 1位オッズがこれ未満ならレースを skip。
        odds_high: 1位オッズがこれを超えたらレースを skip。
        max_bets_per_race: 1 レースあたりの最大購入点数（1 または 2）。

    Returns:
        購入する combination のリスト（最大 max_bets_per_race 件）
    """
    selected = select_top_n_ev_gap_filter_odds_band(
        predictions, top_n, ev_threshold, ev_gap_threshold, odds_low, odds_high
    )
    if max_bets_per_race <= 0:
        return selected
    return selected[:max_bets_per_race]


def select_top_n_ev_gap_venue_filter(
    predictions: List[Dict[str, Any]],
    top_n: int,
    ev_threshold: float,
    ev_gap_threshold: float,
    venue: Optional[str],
    venue_ev_config: Optional[Dict[str, float]] = None,
) -> List[str]:
    """
    top_n_ev_gap_filter の会場別 EV 閾値版。
    venue_ev_config に venue が含まれる場合はその ev_threshold を使用し、
    そうでなければ ev_threshold をそのまま使用する。

    Args:
        predictions: 予測候補リスト（同一レースの all_combinations）。probability と ratio 必須。
        top_n: 選抜する点数。
        ev_threshold: デフォルト期待リターン閾値。
        ev_gap_threshold: 1位と2位の EV 差の閾値。これ未満ならレースを skip。
        venue: 会場名（例: TODA, SUMINOE）。None のときは ev_threshold のみ使用。
        venue_ev_config: 会場別 ev_threshold。例: {"TODA": 1.23, "SUMINOE": 1.17}。

    Returns:
        購入する combination のリスト（skip 時は []）
    """
    if venue and venue_ev_config and venue in venue_ev_config:
        ev_threshold = venue_ev_config[venue]
    return select_top_n_ev_gap_filter(
        predictions, top_n, ev_threshold, ev_gap_threshold=ev_gap_threshold
    )


def select_top_n_ev_power_prob(
    predictions: List[Dict[str, Any]],
    alpha: float,
    top_n: int,
    ev_threshold: float,
) -> List[str]:
    """
    EV_adj = (pred_prob ** alpha) * odds でスコア化し、
    EV_adj >= ev_threshold の候補のうち EV_adj 降順で top_n 件選ぶ。

    Args:
        predictions: 予測候補リスト（probability と ratio または odds が必要）。
        alpha: 確率のべき乗（0.7〜1.1 等）。alpha=1.0 のとき従来の expected_roi = prob * odds と一致。
        top_n: 選抜する点数。
        ev_threshold: EV_adj 閾値（この値以上のみ対象）。

    Returns:
        購入する combination のリスト
    """
    if top_n <= 0 or not predictions:
        return []
    scored: List[Tuple[float, str]] = []
    for c in predictions:
        prob = _get_score(c)
        ratio = _get_odds_ratio(c)
        if ratio is None or ratio <= 0:
            continue
        ev_adj = (prob ** alpha) * ratio
        if ev_adj >= ev_threshold:
            comb = _get_combination(c)
            if comb:
                scored.append((ev_adj, comb))
    scored.sort(key=lambda x: -x[0])
    return [comb for _, comb in scored[:top_n]]


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
    if strategy == STRATEGY_TOP_N_EV_CONFIDENCE:
        confidence_type = (kwargs.get("confidence_type") or CONFIDENCE_PRED_PROB).strip().lower()
        return select_top_n_ev_confidence(
            predictions, top_n, ev_threshold, confidence_type=confidence_type
        )
    if strategy == STRATEGY_EV_THRESHOLD_ONLY:
        return select_ev_threshold_only(predictions, ev_threshold)
    if strategy == STRATEGY_RACE_FILTERED_TOP_N_EV:
        from kyotei_predictor.strategies.race_filtered_top_n_ev import select_race_filtered_top_n_ev
        ev_min = float(kwargs.get("race_ev_min", 1.15))
        prob_gap_min = float(kwargs.get("prob_gap_min", 0.05))
        entropy_max = float(kwargs.get("entropy_max", 1.7))
        candidate_min = int(kwargs.get("candidate_min", 1))
        ev_threshold_for_count = float(kwargs.get("ev_threshold_for_count", ev_min))
        return select_race_filtered_top_n_ev(
            predictions,
            top_n,
            ev_threshold,
            ev_min=ev_min,
            prob_gap_min=prob_gap_min,
            entropy_max=entropy_max,
            candidate_min=candidate_min,
            ev_threshold_for_count=ev_threshold_for_count,
        )
    if strategy == STRATEGY_TOP_N_EV_PROB_POOL:
        pool_k = int(kwargs.get("pool_k", 5))
        confidence_type = (kwargs.get("confidence_type") or "").strip().lower() or None
        return select_top_n_ev_prob_pool(
            predictions, pool_k, top_n, ev_threshold, confidence_type=confidence_type
        )
    if strategy == STRATEGY_TOP_N_EV_POWER_PROB:
        alpha = float(kwargs.get("alpha", 1.0))
        return select_top_n_ev_power_prob(predictions, alpha, top_n, ev_threshold)
    if strategy == STRATEGY_TOP_N_EV_GAP_FILTER:
        ev_gap_threshold = float(kwargs.get("ev_gap_threshold", 0.05))
        selected = select_top_n_ev_gap_filter(
            predictions, top_n, ev_threshold, ev_gap_threshold=ev_gap_threshold
        )
        max_bets_per_race = kwargs.get("max_bets_per_race")
        if max_bets_per_race is not None and int(max_bets_per_race) > 0:
            selected = selected[: int(max_bets_per_race)]
        return selected
    if strategy == STRATEGY_TOP_N_EV_GAP_VENUE_FILTER:
        ev_gap_threshold = float(kwargs.get("ev_gap_threshold", 0.07))
        venue = kwargs.get("venue")
        venue_ev_config = kwargs.get("venue_ev_config") or {}
        return select_top_n_ev_gap_venue_filter(
            predictions,
            top_n,
            ev_threshold,
            ev_gap_threshold=ev_gap_threshold,
            venue=venue,
            venue_ev_config=venue_ev_config,
        )
    if strategy == STRATEGY_TOP_N_EV_GAP_FILTER_ENTROPY:
        ev_gap_threshold = float(kwargs.get("ev_gap_threshold", 0.05))
        entropy_threshold = float(kwargs.get("entropy_threshold", 1.5))
        return select_top_n_ev_gap_filter_entropy(
            predictions,
            top_n,
            ev_threshold,
            ev_gap_threshold=ev_gap_threshold,
            entropy_threshold=entropy_threshold,
        )
    if strategy == STRATEGY_TOP_N_EV_GAP_FILTER_ODDS_BAND:
        ev_gap_threshold = float(kwargs.get("ev_gap_threshold", 0.07))
        odds_low = float(kwargs.get("odds_low", 1.2))
        odds_high = float(kwargs.get("odds_high", 25.0))
        return select_top_n_ev_gap_filter_odds_band(
            predictions,
            top_n,
            ev_threshold,
            ev_gap_threshold=ev_gap_threshold,
            odds_low=odds_low,
            odds_high=odds_high,
        )
    if strategy == STRATEGY_TOP_N_EV_GAP_FILTER_ODDS_BAND_BET_LIMIT:
        ev_gap_threshold = float(kwargs.get("ev_gap_threshold", 0.07))
        odds_low = float(kwargs.get("odds_low", 1.3))
        odds_high = float(kwargs.get("odds_high", 25.0))
        max_bets_per_race = int(kwargs.get("max_bets_per_race", 1))
        return select_top_n_ev_gap_filter_odds_band_bet_limit(
            predictions,
            top_n,
            ev_threshold,
            ev_gap_threshold=ev_gap_threshold,
            odds_low=odds_low,
            odds_high=odds_high,
            max_bets_per_race=max_bets_per_race,
        )
    if strategy == STRATEGY_TOP_N_EV_CONDITIONAL_PROB_GAP:
        band_edges = kwargs.get("band_edges")
        band_params = kwargs.get("band_params")
        if not band_edges or not band_params or len(band_params) != len(band_edges) + 1:
            return select_top_n_ev(predictions, top_n, ev_threshold)
        return select_top_n_ev_conditional_prob_gap(predictions, band_edges, band_params)
    if strategy == STRATEGY_EV:
        result = select_ev(
            predictions,
            ev_threshold=ev_threshold,
            top_n_fallback=top_n,
            return_metadata=return_metadata,
        )
        return result
    return select_single(predictions)
