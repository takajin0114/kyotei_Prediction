"""
買い目選定（ベッティング戦略）パッケージ

予測結果（候補とスコア）を受け取り、「どの買い目を買うか」を判断する。
予測モジュールの責務とは分離する。
"""

from .strategy import (
    select_bets,
    BettingStrategy,
    STRATEGY_SINGLE,
    STRATEGY_TOP_N,
    STRATEGY_THRESHOLD,
    STRATEGY_EV,
)

__all__ = [
    "select_bets",
    "BettingStrategy",
    "STRATEGY_SINGLE",
    "STRATEGY_TOP_N",
    "STRATEGY_THRESHOLD",
    "STRATEGY_EV",
]
