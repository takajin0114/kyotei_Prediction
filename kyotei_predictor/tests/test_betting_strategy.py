#!/usr/bin/env python3
"""
買い目選定（betting strategy）の単体テスト。

- betting strategy の切り替えが効く
- single / top_n / threshold が期待どおり動作する
"""

import pytest


def _candidates(n: int = 5):
    """テスト用候補リスト（combination, probability）"""
    return [
        {"combination": "1-2-3", "probability": 0.15, "rank": 1},
        {"combination": "2-1-3", "probability": 0.12, "rank": 2},
        {"combination": "1-3-2", "probability": 0.10, "rank": 3},
        {"combination": "3-1-2", "probability": 0.08, "rank": 4},
        {"combination": "2-3-1", "probability": 0.05, "rank": 5},
    ][:n]


def test_select_bets_single():
    """常に1点買い（1位のみ）"""
    from kyotei_predictor.tools.betting import select_bets, STRATEGY_SINGLE

    cand = _candidates()
    out = select_bets(cand, strategy=STRATEGY_SINGLE)
    assert out == ["1-2-3"]


def test_select_bets_top_n():
    """上位N点買い"""
    from kyotei_predictor.tools.betting import select_bets, STRATEGY_TOP_N

    cand = _candidates()
    out = select_bets(cand, strategy=STRATEGY_TOP_N, top_n=3)
    assert out == ["1-2-3", "2-1-3", "1-3-2"]

    out2 = select_bets(cand, strategy=STRATEGY_TOP_N, top_n=10)
    assert len(out2) == 5


def test_select_bets_threshold():
    """スコア閾値以上のみ買う"""
    from kyotei_predictor.tools.betting import select_bets, STRATEGY_THRESHOLD

    cand = _candidates()
    out = select_bets(cand, strategy=STRATEGY_THRESHOLD, score_threshold=0.10)
    assert set(out) == {"1-2-3", "2-1-3", "1-3-2"}

    out_low = select_bets(cand, strategy=STRATEGY_THRESHOLD, score_threshold=0.20)
    assert out_low == []


def test_select_bets_empty_candidates():
    """候補が空のときは空リスト"""
    from kyotei_predictor.tools.betting import select_bets, STRATEGY_SINGLE, STRATEGY_TOP_N

    assert select_bets([], strategy=STRATEGY_SINGLE) == []
    assert select_bets([], strategy=STRATEGY_TOP_N, top_n=3) == []


def test_select_bets_default_is_single():
    """戦略未指定時は 1点買い"""
    from kyotei_predictor.tools.betting import select_bets

    cand = _candidates()
    out = select_bets(cand)
    assert out == ["1-2-3"]
