"""
レースデータ読込のリポジトリインターフェース。

学習・検証・比較はこの interface 経由でデータを取得し、
JSON 直読 / DB 読込を差し替え可能にする。
返り値は既存コード互換の dict ベース（将来 dataclass 化しやすい形）。
"""

from typing import Dict, List, Optional, Protocol, Tuple, Any


class RaceDataRepositoryProtocol(Protocol):
    """レースデータ読込のプロトコル。JSON/DB 実装が共通で満たす interface。"""

    def load_race(
        self,
        race_date: str,
        venue: str,
        race_number: int,
    ) -> Optional[Dict[str, Any]]:
        """
        1 レース分の race_data 辞書を取得する。
        存在しなければ None。verify / 予測対象の 1 レース取得に使用。
        """
        ...

    def load_races_between(
        self,
        start_date: str,
        end_date: str,
        max_samples: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        期間内のレースデータを取得する（学習用）。
        各要素は race_data 辞書（race_records 等）。着順の有無は呼び出し側で判定。
        max_samples 指定時はその件数で打ち切り（None で全件）。
        """
        ...

    def load_races_by_date(
        self,
        race_date: str,
        venues: Optional[List[str]] = None,
    ) -> List[Tuple[Dict[str, Any], str, int]]:
        """
        指定日のレース一覧を取得する（予測用）。
        返り値: [(race_data, venue, race_number), ...]。
        venues 指定時はその会場のみ。None で全会場。
        """
        ...

    def get_odds(
        self,
        race_date: str,
        venue: str,
        race_number: int,
    ) -> Optional[Dict[str, Any]]:
        """
        1 レース分の odds_data 辞書を取得する。無ければ None。
        DB リポジトリでは DB から、JSON リポジトリでは data_dir の odds_data_*.json から取得。
        """
        ...
