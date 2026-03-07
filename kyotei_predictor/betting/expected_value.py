"""
EV（期待値）計算。

expected_roi = probability × odds（1.0 で元金、1.05 で 5% プラス）。
閾値比較（expected_roi >= ev_threshold）に利用する。
"""

from typing import Optional


def expected_roi(probability: float, odds: float) -> float:
    """
    期待リターン（expected_roi）を計算する。

    EV = probability × odds
    例: 確率 0.1、オッズ 15 倍 → 1.5（150% の期待リターン）

    Args:
        probability: 的中確率（0〜1）
        odds: オッズ（倍率）

    Returns:
        expected_roi（1.0 で元金、1.05 で 5% プラス）
    """
    return probability * odds


def ev_above_threshold(probability: float, odds: float, ev_threshold: float) -> bool:
    """
    期待リターンが閾値以上かどうかを返す。

    Args:
        probability: 的中確率（0〜1）
        odds: オッズ（倍率）
        ev_threshold: 閾値（例: 1.10 = 10% プラス）

    Returns:
        expected_roi >= ev_threshold なら True
    """
    if odds <= 0:
        return False
    return expected_roi(probability, odds) >= ev_threshold
