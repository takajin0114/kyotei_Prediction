"""
DB ベースのレースデータリポジトリ実装。

SQLite (RaceDB) からレースデータを取得する。学習・検証の主データ源として利用。
SQL は RaceDB 内に閉じ込められており、本リポジトリはそのラッパー。
"""

from typing import Any, Dict, List, Optional, Tuple

from kyotei_predictor.data.race_db import RaceDB


class DbRaceDataRepository:
    """RaceDB を用いたレースデータ読込。学習・検証・比較の DB 対応用。"""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._db: Optional[RaceDB] = None

    def _get_db(self) -> RaceDB:
        if self._db is None:
            self._db = RaceDB(self.db_path)
        return self._db

    def load_race(
        self,
        race_date: str,
        venue: str,
        race_number: int,
    ) -> Optional[Dict[str, Any]]:
        """1 レース分の race_data 辞書を DB から取得する。"""
        return self._get_db().get_race_json(race_date, venue, race_number)

    def load_races_between(
        self,
        start_date: str,
        end_date: str,
        max_samples: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        期間内のレースを取得する（学習用）。
        race と odds のペアが存在するレースのみ取得（既存 import 方針に合わせる）。
        """
        db = self._get_db()
        pairs = db.get_race_odds_pairs(date_from=start_date, date_to=end_date)
        result: List[Dict[str, Any]] = []
        for race_date, stadium, race_number in pairs:
            if max_samples is not None and len(result) >= max_samples:
                break
            data = db.get_race_json(race_date, stadium, race_number)
            if data is not None:
                result.append(data)
        return result

    def load_races_by_date(
        self,
        race_date: str,
        venues: Optional[List[str]] = None,
    ) -> List[Tuple[Dict[str, Any], str, int]]:
        """指定日のレース一覧を (race_data, venue, race_number) のリストで返す。"""
        db = self._get_db()
        pairs = db.get_race_odds_pairs(date_from=race_date, date_to=race_date)
        result: List[Tuple[Dict[str, Any], str, int]] = []
        for d, stadium, race_number in pairs:
            if d != race_date:
                continue
            if venues is not None and stadium not in venues:
                continue
            data = db.get_race_json(race_date, stadium, race_number)
            if data is not None:
                result.append((data, stadium, race_number))
        return result

    def close(self) -> None:
        """接続を閉じる。長時間運用時は明示的に呼ぶ。"""
        if self._db is not None:
            self._db.close()
            self._db = None
