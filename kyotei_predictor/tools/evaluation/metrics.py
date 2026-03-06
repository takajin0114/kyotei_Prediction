#!/usr/bin/env python3
"""
評価指標の分離モジュール

hit_rate, mean_reward, ROI, 投資額, 払戻額, 的中件数を分解して保持し、
optimize_for に応じて最終 objective を組み立てる。
"""

from typing import Dict, Any, List, Optional
import numpy as np


# 許容する optimize_for の値
OPTIMIZE_FOR_HIT_RATE = "hit_rate"
OPTIMIZE_FOR_MEAN_REWARD = "mean_reward"
OPTIMIZE_FOR_ROI = "roi"
OPTIMIZE_FOR_HYBRID = "hybrid"
OPTIMIZE_FOR_VALID = (OPTIMIZE_FOR_HIT_RATE, OPTIMIZE_FOR_MEAN_REWARD, OPTIMIZE_FOR_ROI, OPTIMIZE_FOR_HYBRID)


def compute_metrics_from_episodes(
    rewards: List[float],
    hit_count: int,
    payouts: Optional[List[float]] = None,
    bet_amounts: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    エピソードごとの報酬・的中・払戻・賭け金から評価指標を算出する。

    Args:
        rewards: エピソードごとの報酬リスト
        hit_count: 的中したエピソード数
        payouts: エピソードごとの払戻額（None の場合は 0 で埋めて ROI は 0 に近づく）
        bet_amounts: エピソードごとの賭け金（None の場合は 100 とみなす）

    Returns:
        hit_rate, mean_reward, roi_pct, total_bet, total_payout, hit_count, n_episodes 等を含む辞書
    """
    n = len(rewards)
    if n == 0:
        return {
            "hit_rate": 0.0,
            "mean_reward": 0.0,
            "std_reward": 0.0,
            "roi_pct": 0.0,
            "total_bet": 0.0,
            "total_payout": 0.0,
            "hit_count": 0,
            "n_episodes": 0,
        }

    payouts = payouts if payouts is not None else [0.0] * n
    bet_amounts = bet_amounts if bet_amounts is not None else [100.0] * n
    # 長さを揃える
    payouts = (payouts + [0.0] * n)[:n]
    bet_amounts = (bet_amounts + [100.0] * n)[:n]

    total_bet = sum(bet_amounts)
    total_payout = sum(payouts)
    roi_pct = (total_payout / total_bet * 100.0) if total_bet > 0 else 0.0

    return {
        "hit_rate": hit_count / n,
        "mean_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "roi_pct": roi_pct,
        "total_bet": total_bet,
        "total_payout": total_payout,
        "hit_count": hit_count,
        "n_episodes": n,
    }


def objective_from_metrics(metrics: Dict[str, Any], optimize_for: str = OPTIMIZE_FOR_HYBRID) -> float:
    """
    分解された評価指標から、optimize_for に応じた単一の objective 値を返す。

    - hit_rate: hit_rate をそのまま（0〜1）を 100 倍したようなスケールで返す（最大化したいので hit_rate * 100）
    - mean_reward: mean_reward をそのまま返す（スケールが大きいので 1000 で割るなどは呼び出し側で調整可）
    - roi: roi_pct をそのまま返す（% 値）
    - hybrid: 従来互換の合成スコア（hit_rate * 100 + mean_reward / 1000）

    Args:
        metrics: compute_metrics_from_episodes の戻り値
        optimize_for: "hit_rate" | "mean_reward" | "roi" | "hybrid"

    Returns:
        最大化したいスカラー値
    """
    if optimize_for not in OPTIMIZE_FOR_VALID:
        optimize_for = OPTIMIZE_FOR_HYBRID

    hit_rate = metrics.get("hit_rate", 0.0)
    mean_reward = metrics.get("mean_reward", 0.0)
    roi_pct = metrics.get("roi_pct", 0.0)

    if optimize_for == OPTIMIZE_FOR_HIT_RATE:
        return hit_rate * 100.0
    if optimize_for == OPTIMIZE_FOR_MEAN_REWARD:
        return mean_reward
    if optimize_for == OPTIMIZE_FOR_ROI:
        return roi_pct
    # hybrid: 従来互換
    return hit_rate * 100.0 + mean_reward / 1000.0


def merge_info_into_episode_results(
    episode_rewards: List[float],
    episode_infos: List[Dict[str, Any]],
) -> tuple:
    """
    エピソードごとの reward と info のリストから、hit_count / payouts / bet_amounts を抽出する。

    info は env.step の戻り値の info（DummyVecEnv の場合は info[0]）。
    キー: arrival, payout, bet_amount, hit を想定。

    Returns:
        (hit_count, payouts, bet_amounts)
    """
    hit_count = 0
    payouts: List[float] = []
    bet_amounts: List[float] = []
    for inf in episode_infos:
        # VecEnv の場合は inf が list で inf[0] が実際の dict のことがある
        i = inf[0] if isinstance(inf, (list, tuple)) and len(inf) > 0 else inf
        if isinstance(i, dict):
            hit_count += i.get("hit", 0)
            payouts.append(float(i.get("payout", 0)))
            bet_amounts.append(float(i.get("bet_amount", 100)))
        else:
            payouts.append(0.0)
            bet_amounts.append(100.0)
    # 長さを rewards に揃える（足りない分は 0 / 100 で埋める）
    n = len(episode_rewards)
    while len(payouts) < n:
        payouts.append(0.0)
    while len(bet_amounts) < n:
        bet_amounts.append(100.0)
    payouts = payouts[:n]
    bet_amounts = bet_amounts[:n]
    return hit_count, payouts, bet_amounts
