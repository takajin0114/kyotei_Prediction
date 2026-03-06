"""
EV（期待値）計算のドメインロジック。

expected_roi = probability × odds で計算し、
閾値比較（expected_roi > ev_threshold）に利用する。
"""


def compute_expected_value(probability: float, odds: float) -> float:
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
