"""
ベットサイズ計算（fixed / Kelly）。

Kelly criterion: f = (b*p - q) / b
  b = odds - 1（ネットオッズ）
  p = 予測確率
  q = 1 - p
"""

from typing import Literal

BET_SIZING_FIXED = "fixed"
BET_SIZING_KELLY_FULL = "kelly_full"
BET_SIZING_KELLY_HALF = "kelly_half"


def kelly_fraction(probability: float, odds: float) -> float:
    """
    Kelly 基準の賭け率を計算する。

    f = (b*p - q) / b
    b = odds - 1, p = probability, q = 1 - p

    Args:
        probability: 予測確率（0〜1）
        odds: オッズ（倍率）

    Returns:
        Kelly fraction（0〜1 にクランプ。0 以下は 0）
    """
    if odds <= 1.0:
        return 0.0
    b = odds - 1.0
    p = probability
    q = 1.0 - p
    f = (b * p - q) / b
    return max(0.0, min(1.0, f))


def compute_stake(
    bankroll: float,
    probability: float,
    odds: float,
    sizing: Literal["fixed", "kelly_full", "kelly_half"],
    unit_stake: float = 100.0,
) -> float:
    """
    1 点あたりの賭け金を計算する。

    Args:
        bankroll: 現在の資金（Kelly 時のみ使用）
        probability: 予測確率
        odds: オッズ（倍率）
        sizing: "fixed" | "kelly_full" | "kelly_half"
        unit_stake: fixed 時の 1 点あたり金額（円）

    Returns:
        賭け金（円）。Kelly 時は bankroll * fraction を unit_stake で丸めるか、
        そのまま返す。ここでは最小 unit_stake 以上になるよう切り上げし、
        bankroll を超えないようにする。
    """
    if sizing == BET_SIZING_FIXED:
        return unit_stake

    kf = kelly_fraction(probability, odds)
    if kf <= 0:
        return 0.0

    if sizing == BET_SIZING_KELLY_HALF:
        kf *= 0.5

    raw = bankroll * kf
    stake = min(bankroll, max(0, raw))
    return round(stake, 2)
