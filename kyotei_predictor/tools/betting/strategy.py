#!/usr/bin/env python3
"""
購入判断ロジック（ベッティング戦略）の分離

予測結果は「候補とスコア」を出すだけとする。
実際に「買う / 買わない」を判断するのはこのモジュールの責務。
将来 EV ベースに置き換えやすいインターフェースにする。
"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod


# 戦略名（設定で指定する文字列）
STRATEGY_SINGLE = "single"       # 常に1点買い（1位予想のみ）
STRATEGY_TOP_N = "top_n"         # 上位N点買い
STRATEGY_THRESHOLD = "threshold" # スコア閾値以上のみ買う
STRATEGY_EV = "ev"               # EV ベース（将来拡張。現状は top_n 相当でフォールバック）


def _get_combination(c: Dict[str, Any]) -> str:
    """候補辞書から combination 文字列を取得（'1-2-3' 形式）"""
    return (c.get("combination") or "").strip()


def _get_score(c: Dict[str, Any]) -> float:
    """候補辞書からスコア（確率）を取得。キーは probability または score。"""
    return float(c.get("probability", c.get("score", 0.0)))


def _get_expected_value(c: Dict[str, Any]) -> Optional[float]:
    """候補辞書から期待値を取得（EV 戦略用。無ければ None）"""
    ev = c.get("expected_value")
    if ev is None:
        return None
    try:
        return float(ev)
    except (TypeError, ValueError):
        return None


class BettingStrategy(ABC):
    """購入判断の抽象基底クラス。将来 EV ベース等を追加しやすいようにする。"""

    @abstractmethod
    def select(self, candidates: List[Dict[str, Any]], **kwargs: Any) -> List[str]:
        """
        候補リストから購入する組み合わせ（combination 文字列）のリストを返す。

        Args:
            candidates: 予測結果の候補リスト。各要素は combination, probability 等を持つ辞書。
            **kwargs: 戦略ごとのパラメータ（top_n, score_threshold 等）

        Returns:
            購入する combination のリスト（例: ["1-2-3", "2-1-3"]）
        """
        pass


class SingleBettingStrategy(BettingStrategy):
    """常に1点買い（1位予想のみ）"""

    def select(self, candidates: List[Dict[str, Any]], **kwargs: Any) -> List[str]:
        if not candidates:
            return []
        c = _get_combination(candidates[0])
        return [c] if c else []


class TopNBettingStrategy(BettingStrategy):
    """上位N点買い。N は kwargs の top_n（デフォルト 3）"""

    def select(self, candidates: List[Dict[str, Any]], **kwargs: Any) -> List[str]:
        top_n = int(kwargs.get("top_n", 3))
        if top_n <= 0 or not candidates:
            return []
        out: List[str] = []
        for c in candidates[:top_n]:
            comb = _get_combination(c)
            if comb:
                out.append(comb)
        return out


class ThresholdBettingStrategy(BettingStrategy):
    """スコア（確率）が閾値以上のみ買う。閾値は kwargs の score_threshold（デフォルト 0.05）"""

    def select(self, candidates: List[Dict[str, Any]], **kwargs: Any) -> List[str]:
        threshold = float(kwargs.get("score_threshold", 0.05))
        out: List[str] = []
        for c in candidates:
            if _get_score(c) >= threshold:
                comb = _get_combination(c)
                if comb:
                    out.append(comb)
        return out


class EVBettingStrategy(BettingStrategy):
    """
    EV ベースの購入判断（将来拡張用）。
    現時点では expected_value が閾値以上なら買う、なければ上位 top_n でフォールバック。
    TODO: 確率とオッズから EV を計算し、閾値以上のみ購入する実装に発展させる。
    """

    def select(self, candidates: List[Dict[str, Any]], **kwargs: Any) -> List[str]:
        ev_threshold = float(kwargs.get("ev_threshold", 0.0))
        top_n_fallback = int(kwargs.get("top_n", 5))
        out: List[str] = []
        for c in candidates:
            ev = _get_expected_value(c)
            if ev is not None and ev >= ev_threshold:
                comb = _get_combination(c)
                if comb:
                    out.append(comb)
        if not out:
            # フォールバック: 上位 N 点
            for c in candidates[:top_n_fallback]:
                comb = _get_combination(c)
                if comb:
                    out.append(comb)
        return out


def _strategy_from_name(name: str) -> BettingStrategy:
    name = (name or "").strip().lower()
    if name == STRATEGY_SINGLE:
        return SingleBettingStrategy()
    if name == STRATEGY_TOP_N:
        return TopNBettingStrategy()
    if name == STRATEGY_THRESHOLD:
        return ThresholdBettingStrategy()
    if name == STRATEGY_EV:
        return EVBettingStrategy()
    # デフォルト: 1点買い
    return SingleBettingStrategy()


def select_bets(
    candidates: List[Dict[str, Any]],
    strategy: str = STRATEGY_SINGLE,
    top_n: int = 3,
    score_threshold: float = 0.05,
    ev_threshold: float = 0.0,
    **extra_kwargs: Any,
) -> List[str]:
    """
    予測候補から購入する買い目を選ぶ。

    Args:
        candidates: 予測結果の候補リスト（combination, probability 等を持つ辞書のリスト）
        strategy: "single" | "top_n" | "threshold" | "ev"
        top_n: strategy=top_n のときの N
        score_threshold: strategy=threshold のときの閾値
        ev_threshold: strategy=ev のときの EV 閾値
        **extra_kwargs: その他戦略に渡すパラメータ

    Returns:
        購入する combination のリスト（例: ["1-2-3", "2-1-3"]）
    """
    s = _strategy_from_name(strategy)
    kwargs = {
        "top_n": top_n,
        "score_threshold": score_threshold,
        "ev_threshold": ev_threshold,
        **extra_kwargs,
    }
    return s.select(candidates, **kwargs)
