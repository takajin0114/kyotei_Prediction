"""
Kelly criterion による賭け率計算。

edge = prob * odds - 1
kelly_fraction = max(edge / (odds - 1), 0)

安全のため capped Kelly（最大 5%）を採用可能。
"""

KELLY_CAP_DEFAULT = 0.05


def kelly_fraction(prob: float, odds: float) -> float:
    """
    Kelly 基準の賭け率を計算する。

    edge = prob * odds - 1
    kelly = max(edge / (odds - 1), 0)

    Args:
        prob: 的中確率（0〜1）
        odds: オッズ（倍率）

    Returns:
        賭け率（0以上）。odds <= 1 のとき 0
    """
    if odds <= 1:
        return 0.0
    edge = prob * odds - 1.0
    return max(edge / (odds - 1.0), 0.0)


def kelly_capped(prob: float, odds: float, cap: float = KELLY_CAP_DEFAULT) -> float:
    """
    安全のため cap で上限を設けた Kelly 賭け率。

    kelly = min(kelly_fraction(prob, odds), cap)

    Args:
        prob: 的中確率（0〜1）
        odds: オッズ（倍率）
        cap: 上限（デフォルト 0.05 = 5%）

    Returns:
        賭け率（0〜cap）
    """
    kf = kelly_fraction(prob, odds)
    return min(kf, cap)
