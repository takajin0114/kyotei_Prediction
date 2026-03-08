"""
ベットサイズ計算（fixed / Kelly）。

Kelly criterion: kelly.py の kelly_fraction を利用。
kelly_capped: 安全のため cap 0.05 で上限。
"""

from typing import Literal

from kyotei_predictor.betting.kelly import kelly_fraction, kelly_capped

BET_SIZING_FIXED = "fixed"
BET_SIZING_KELLY_FULL = "kelly_full"
BET_SIZING_KELLY_HALF = "kelly_half"
BET_SIZING_KELLY_CAPPED = "kelly_capped"  # cap 0.05


def compute_stake(
    bankroll: float,
    probability: float,
    odds: float,
    sizing: Literal["fixed", "kelly_full", "kelly_half", "kelly_capped"],
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

    if sizing == BET_SIZING_KELLY_CAPPED:
        kf = kelly_capped(probability, odds, cap=0.05)
    else:
        kf = kelly_fraction(probability, odds)
    if kf <= 0:
        return 0.0

    if sizing == BET_SIZING_KELLY_HALF:
        kf *= 0.5

    raw = bankroll * kf
    stake = min(bankroll, max(0, raw))
    return round(stake, 2)
