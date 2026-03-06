"""
ベッティングまわりのドメインモデル（データ構造のみ）。

実際の選定ロジックは tools.betting / utils.betting_selector に残し、
domain では「候補」「選定結果」の形を定義する。
TODO: 段階的に tools から domain を参照する形に寄せる。
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PredictionCandidate:
    """1組み合わせの予測候補（combination + スコア等）。"""
    combination: str
    probability: float
    score: Optional[float] = None
    ratio: Optional[float] = None  # オッズ
    expected_value: Optional[float] = None

    def to_dict(self) -> dict:
        d = {"combination": self.combination, "probability": self.probability}
        if self.score is not None:
            d["score"] = self.score
        if self.ratio is not None:
            d["ratio"] = self.ratio
        if self.expected_value is not None:
            d["expected_value"] = self.expected_value
        return d


@dataclass
class SelectedBet:
    """選定された買い目（1組み合わせ）。"""
    combination: str

    def to_dict(self) -> dict:
        return {"combination": self.combination}
